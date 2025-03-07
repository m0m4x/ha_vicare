"""The ViCare integration."""
import enum
import logging

from PyViCare.PyViCareDevice import Device
from PyViCare.PyViCareFuelCell import FuelCell
from PyViCare.PyViCareGazBoiler import GazBoiler
from PyViCare.PyViCareHeatPump import HeatPump

class Solar(Device):

    def getSolarCollectorTemperature(self):
        _LOGGER.info('Ci siamo')
        _LOGGER.info(str(self.service.getProperty("heating.solar.sensors.temperature.collector")["properties"]["value"]["value"]))
        return float(self.service.getProperty("heating.solar.sensors.temperature.collector")["properties"]["value"]["value"])

    def getSolarStorageTemperature(self):
        return float(self.service.getProperty("heating.solar.sensors.temperature.dhw")["properties"]["value"]["value"])

    def getSolarPowerProduction(self):
        return self.service.getProperty("heating.solar.power.production")["properties"]["day"]["value"]

    def getSolarPumpActive(self):
        status = self.service.getProperty("heating.solar.pumps.circuit")[
            "properties"]["status"]["value"]
        return status == 'on'

import voluptuous as vol

from homeassistant.const import (
    CONF_CLIENT_ID,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_SCAN_INTERVAL,
    CONF_USERNAME,
)
from homeassistant.helpers import discovery
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.storage import STORAGE_DIR

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["climate", "sensor", "binary_sensor", "water_heater"]

DOMAIN = "vicare"
VICARE_API = "api"
VICARE_NAME = "name"
VICARE_HEATING_TYPE = "heating_type"
VICARE_SOLAR = "solar"

CONF_SOLAR = "solar"
CONF_CIRCUIT = "circuit"
CONF_HEATING_TYPE = "heating_type"
DEFAULT_HEATING_TYPE = "generic"


class HeatingType(enum.Enum):
    """Possible options for heating type."""

    generic = "generic"
    gas = "gas"
    heatpump = "heatpump"
    fuelcell = "fuelcell"


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_CLIENT_ID): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL, default=60): vol.All(
                    cv.time_period, lambda value: value.total_seconds()
                ),
                vol.Optional(CONF_CIRCUIT): int,
                vol.Optional(CONF_NAME, default="ViCare"): cv.string,
                vol.Optional(CONF_HEATING_TYPE, default=DEFAULT_HEATING_TYPE): cv.enum(
                    HeatingType
                ),
                vol.Optional(CONF_SOLAR, default=True): cv.boolean,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Create the ViCare component."""
    conf = config[DOMAIN]
    params = {"token_file": hass.config.path(STORAGE_DIR, "vicare_token.save")}
    if conf.get(CONF_CIRCUIT) is not None:
        params["circuit"] = conf[CONF_CIRCUIT]

    params["cacheDuration"] = conf.get(CONF_SCAN_INTERVAL)
    params["client_id"] = conf.get(CONF_CLIENT_ID)
    heating_type = conf[CONF_HEATING_TYPE]
    solar = conf[CONF_SOLAR]

    try:
        if heating_type == HeatingType.gas:
            vicare_api = GazBoiler(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        elif heating_type == HeatingType.heatpump:
            vicare_api = HeatPump(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        elif heating_type == HeatingType.fuelcell:
            vicare_api = FuelCell(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        else:
            vicare_api = Device(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
        #if solar is True:
        SuperDevice = type('SuperDevice', (GazBoiler, Solar), dict())
        vicare_api = SuperDevice(conf[CONF_USERNAME], conf[CONF_PASSWORD], **params)
    except AttributeError:
        _LOGGER.error(
            "Failed to create PyViCare API client. Please check your credentials"
        )
        return False

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][VICARE_API] = vicare_api
    hass.data[DOMAIN][VICARE_NAME] = conf[CONF_NAME]
    hass.data[DOMAIN][VICARE_HEATING_TYPE] = heating_type
    hass.data[DOMAIN][VICARE_SOLAR] = heating_type

    for platform in PLATFORMS:
        discovery.load_platform(hass, platform, DOMAIN, {}, config)

    return True
