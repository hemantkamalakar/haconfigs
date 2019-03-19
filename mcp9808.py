"""
Support for showing MCP numbers.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.MCP/
"""
import logging
import time
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME, CONF_UNIT_OF_MEASUREMENT)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

CONF_I2C_ADDRESS = 'i2c_address'
CONF_I2C_BUS = 'i2c_bus'


DEFAULT_NAME = 'MCP Sensor'
DEFAULT_MIN = 0
DEFAULT_MAX = 20
DEFAULT_I2C_ADDRESS = '0x18'
DEFAULT_I2C_BUS = 1

ICON = 'mdi:hanger'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_I2C_BUS, default=DEFAULT_I2C_BUS): vol.Coerce(int),
    vol.Optional(CONF_I2C_ADDRESS, default=DEFAULT_I2C_ADDRESS): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
})


async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
    import smbus    
    """Set up the MCP number sensor."""
    #bus = smbus.SMBus(1) 
    bus = smbus.SMBus(config.get(CONF_I2C_BUS))
    name = config.get(CONF_NAME)
    unit = config.get(CONF_UNIT_OF_MEASUREMENT)
    i2c_address = config.get(CONF_I2C_ADDRESS)

    async_add_entities([MCPSensor(name, bus, i2c_address,  unit)], True)


class MCPSensor(Entity):
    """Representation of a MCP number sensor."""

    def __init__(self, name, bus, i2c_address,  unit_of_measurement):
        """Initialize the MCP sensor."""
        self._name = name
        self._bus = bus
        self._i2c_address = i2c_address
        self._unit_of_measurement = unit_of_measurement
        self._state = None

    @property
    def name(self):
        """Return the name of the device."""
        return self._name
 
    @property
    def bus(self):
        """Return the bus of the device."""
        return self._bus
    
    @property
    def i2c_address(self):
        """Return the bus of the device."""
        return self._i2c_address

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return ICON

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return self._unit_of_measurement


    async def async_update(self):
        """Get a new number and updates the states."""
        v = self.bus.read_word_data(self.i2c_address, 0x05)
        hiByte = v & 0x00FF  # SMBus with reversed byte order
        loByte = (v >> 8) & 0x00FF
        hiByte = hiByte  & 0x1F # clear flag bit
        if hiByte & 0x10 == 0x10:  # temp < 0
            hiByte = hiByte & 0x0F  # clear sign
            temp = 256 - hiByte * 16 + loByte / 16.0 # scale
        else:
            temp = hiByte * 16 + loByte / 16.0 # scale
        temp = round(temp, 2)

        self._state = temp