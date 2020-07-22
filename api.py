"""Waste API."""

import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Mapping, Optional

import async_timeout
import aiohttp


XIMMIO_API_BASE_URL = "https://wasteapi.ximmio.com/api/"
XIMMIO_API_ADDRESS_URL = XIMMIO_API_BASE_URL + "FetchAdress"
XIMMIO_API_CALENDAR_URL = XIMMIO_API_BASE_URL + "GetCalendar"
XIMMIO_API_COMPANY_CODES = {
    "ACV Groep": "f8e2844a-095e-48f9-9f98-71fceb51d2c3",
}


class XimmioApiWasteType(Enum):
    GREY = 0
    GREEN = 1
    PAPER = 2
    PACKAGES = 10


class XimmioWasteApiException(Exception):

    pass


class XimmioWasteApi:

    def __init__(
            self,
            post_code: str,
            house_number: str,
            company_code: str,
            request_timeout: int = 10,
            loop=None,
            session=None,
    ):
        self.post_code = post_code
        self.house_number = house_number
        self.company_code = company_code
        self._request_timeout = request_timeout
        self._loop = loop or asyncio.get_event_loop()
        self._session = session or aiohttp.ClientSession(loop=self._loop)
        self._address_id = None

    async def fetch_address(self):
        if self._address_id is not None:
            return self._address_id

        post_data = {
            "postCode": self.post_code,
            "houseNumber": self.house_number,
            "companyCode": self.company_code,
        }
        response_data = await self._post(XIMMIO_API_ADDRESS_URL, data=post_data)
        if not response_data.get("dataList"):
            raise XimmioWasteApiException("Address not found")
        self._address_id = response_data["dataList"][0]["UniqueId"]  # Take any
        return self._address_id

    async def get_calendar(self, end_date_days: int = 56):
        address_id = await self.fetch_address()
        start_date = datetime.today()
        end_date = start_date + timedelta(days=end_date_days)
        post_data = {
            "companyCode": self.company_code,
            "uniqueAddressID": address_id,
            "startDate": start_date.strftime("%Y-%m-%d"),
            "endDate": end_date.strftime("%Y-%m-%d"),
        }
        response_data = await self._post(XIMMIO_API_CALENDAR_URL, data=post_data)

        calendar = {}
        for pickup in response_data["dataList"]:
            pickup_type = pickup["_pickupType"]
            pickup_type_enum = XimmioApiWasteType(pickup_type)
            calendar[pickup_type_enum] = sorted([
                datetime.strptime(pickup_date, "%Y-%m-%dT%H:%M:%S")
                for pickup_date in pickup["pickupDates"] or []
            ])
        return calendar

    async def _post(self, url: str, data: Mapping):
        """Do a post request to a URL."""
        # Do the POST request.
        headers = {
            "User-Agent": "python-ximmio-waste-api/0.0.1",
            "Accept": "application/json, text/plain, */*",
        }
        with async_timeout.timeout(self._request_timeout):
            response = await self._session.request(
                "POST", url, json=data, headers=headers, ssl=True
            )

        if (response.status // 100) in [4, 5]:
            raise XimmioWasteApiException("API not available")

        if "application/json" not in response.headers["Content-Type"]:
            raise XimmioWasteApiException("Cannot parse response")

        return await response.json()
