"""Viessmann ViCare sensor device."""
from contextlib import suppress
import logging

from PyViCare.PyViCare import PyViCareNotSupportedFeatureError, PyViCareRateLimitError
import requests

from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_POWER,
    BinarySensorEntity,
)
from homeassistant.const import CONF_DEVICE_CLASS, CONF_NAME

from . import (
    DOMAIN as VICARE_DOMAIN,
    VICARE_API,
    VICARE_HEATING_TYPE,
    VICARE_SOLAR,
    VICARE_NAME,
    HeatingType,
)

_LOGGER = logging.getLogger(__name__)

CONF_GETTER = "getter"

SENSOR_CIRCULATION_PUMP_ACTIVE = "circulationpump_active"

# gas sensors
SENSOR_BURNER_ACTIVE = "burner_active"

# heatpump sensors
SENSOR_COMPRESSOR_ACTIVE = "compressor_active"

# solar sensors
SENSOR_SOLAR_ACTIVE = "solar_active"

SENSOR_TYPES = {
    SENSOR_CIRCULATION_PUMP_ACTIVE: {
        CONF_NAME: "Circulation pump active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.getCirculationPumpActive(),
    },
    # gas sensors
    SENSOR_BURNER_ACTIVE: {
        CONF_NAME: "Burner active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.getBurnerActive(),
    },
    # heatpump sensors
    SENSOR_COMPRESSOR_ACTIVE: {
        CONF_NAME: "Compressor active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.getCompressorActive(),
    },
    # solar sensors
    SENSOR_SOLAR_ACTIVE: {
        CONF_NAME: "Solar Pump Active",
        CONF_DEVICE_CLASS: DEVICE_CLASS_POWER,
        CONF_GETTER: lambda api: api.getSolarPumpActive(),
    },
}

SENSORS_GENERIC = [SENSOR_CIRCULATION_PUMP_ACTIVE]

SENSORS_SOLAR = [SENSOR_SOLAR_ACTIVE]

SENSORS_BY_HEATINGTYPE = {
    HeatingType.gas: [SENSOR_BURNER_ACTIVE],
    HeatingType.heatpump: [
        SENSOR_COMPRESSOR_ACTIVE,
    ],
    HeatingType.fuelcell: [SENSOR_BURNER_ACTIVE],
}


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Create the ViCare sensor devices."""
    if discovery_info is None:
        return

    vicare_api = hass.data[VICARE_DOMAIN][VICARE_API]
    heating_type = hass.data[VICARE_DOMAIN][VICARE_HEATING_TYPE]
    solar = hass.data[VICARE_DOMAIN][VICARE_SOLAR]

    sensors = SENSORS_GENERIC.copy()

    if heating_type != HeatingType.generic:
        sensors.extend(SENSORS_BY_HEATINGTYPE[heating_type])

    #if solar is True:
    sensors.extend(SENSORS_SOLAR)

    add_entities(
        [
            ViCareBinarySensor(
                hass.data[VICARE_DOMAIN][VICARE_NAME], vicare_api, sensor
            )
            for sensor in sensors
        ]
    )


class ViCareBinarySensor(BinarySensorEntity):
    """Representation of a ViCare sensor."""

    def __init__(self, name, api, sensor_type):
        """Initialize the sensor."""
        self._sensor = SENSOR_TYPES[sensor_type]
        self._name = f"{name} {self._sensor[CONF_NAME]}"
        self._api = api
        self._sensor_type = sensor_type
        self._state = None

    @property
    def available(self):
        """Return True if entity is available."""
        return self._state is not None

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._api.service.id}-{self._sensor_type}"

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def is_on(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def device_class(self):
        """Return the class of this device, from component DEVICE_CLASSES."""
        return self._sensor[CONF_DEVICE_CLASS]

    def update(self):
        """Update state of sensor."""
        try:
            with suppress(PyViCareNotSupportedFeatureError):
                self._state = self._sensor[CONF_GETTER](self._api)
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Unable to retrieve data from ViCare server")
        except ValueError:
            _LOGGER.error("Unable to decode data from ViCare server")
        except PyViCareRateLimitError as limit_exception:
            _LOGGER.error("Vicare API rate limit exceeded: %s", limit_exception)
