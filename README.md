# home-assistant-ximmio-waste-api

Home Assistant custom component to get next waste pick dates from Ximmio waste API.


## Installation

Put this in your Home Assistant custom\_components directory, e.g.:

```
$ cd ~/.homeassistant
$ mkdir custom_components
$ git clone https://github.com/StevenLooman/home-assistant-ximmio-waste-api ximmio-waste-api
```

Add a new platform to your `sensor` object in `configuration.yaml`:

```
sensor:
  - platform: ximmio-waste-api
    post_code: "3900AA"
    house_number: 1
    company: "ACV Groep"
```


## Usage

For new sensors will be created, each showing the next pick up date.


## Adding support for new companies

Currently only "ACV Groep" is supported, but other companies can easily be added. Edit the file `api.py` and extend the `XIMMIO_API_COMPANY_CODES` mapping. Feel free to create a pull request.
