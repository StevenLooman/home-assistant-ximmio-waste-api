"""Ximmio waste API sensor."""

import logging
from datetime import datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import HomeAssistantType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import Throttle

from .api import XIMMIO_API_COMPANY_CODES, XimmioWasteApi, XimmioApiWasteType
from .const import CONF_COMPANY, CONF_HOUSE_NUMBER, CONF_POST_CODE, DOMAIN


_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = timedelta(days=1)


async def async_setup_platform(
    hass: HomeAssistantType, config, add_devices, discovery_info=None
):
    _LOGGER.debug("async_setup_platform(%s, %s)", config, discovery_info)
    company = config[CONF_COMPANY]
    if company not in XIMMIO_API_COMPANY_CODES:
        # XXX TODO: should be done through a schema
        raise RuntimeError("Company not known")

    post_code = config[CONF_POST_CODE]
    house_number = config[CONF_HOUSE_NUMBER]
    company_code = XIMMIO_API_COMPANY_CODES[company]
    ximmio_waste_api = XimmioWasteApi(post_code=post_code, house_number=house_number, company_code=company_code)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="ximmio-waste-api",
        update_method=ximmio_waste_api.get_calendar,
        update_interval=UPDATE_INTERVAL,
    )
    await coordinator.async_refresh()

    add_devices([
        XimmioWasteApiSensor(ximmio_waste_api, XimmioApiWasteType.GREY, coordinator),
        XimmioWasteApiSensor(ximmio_waste_api, XimmioApiWasteType.GREEN, coordinator),
        XimmioWasteApiSensor(ximmio_waste_api, XimmioApiWasteType.PACKAGES, coordinator),
        XimmioWasteApiSensor(ximmio_waste_api, XimmioApiWasteType.PAPER, coordinator),
    ])


class XimmioWasteApiSensor(Entity):

    def __init__(
        self,
        waste_api: XimmioWasteApi,
        waste_type: XimmioApiWasteType,
        coordinator: DataUpdateCoordinator,
    ):
        self._waste_api = waste_api
        self._waste_type = waste_type
        self._coordinator = coordinator

    @property
    def name(self) -> str:
        """Return the name of the entity."""
        return f"{self._waste_type.name} Waste Pickup"

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this sensor."""
        company_code = self._waste_api.company_code
        return f"{DOMAIN}_{company_code}_{self._waste_type.name}"

    @property
    def icon(self) -> str:
        """Icon to use in the frontend, if any."""
        return "mdi:delete-empty"

    @property
    def should_poll(self) -> bool:
        """Return the polling requirement of the entity."""
        return False

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._coordinator.last_update_success

    async def async_update(self):
        """Request an update."""
        await self._coordinator.async_request_refresh()

    async def async_added_to_hass(self) -> None:
        """Subscribe to sensors events."""
        remove_from_coordinator = self._coordinator.async_add_listener(
            self.async_write_ha_state
        )
        self.async_on_remove(remove_from_coordinator)

    @property
    def state(self) -> str:
        """Return the state of the device."""
        pickup_dates = self._coordinator.data.get(self._waste_type)
        if pickup_dates is None:
            return None
        todays_date = datetime.today()
        pickup_dates = [
            pickup_date
            for pickup_date in pickup_dates
            if pickup_date > todays_date
        ]
        next_pickup_date: datetime = min(pickup_dates)
        return next_pickup_date.strftime("%Y-%m-%d")
