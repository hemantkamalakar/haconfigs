"""
MCP9808 Temperature sensor.
"""
import logging
import time
from datetime import timedelta
import voluptuous as vol
import smbus    
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ( CONF_SCAN_INTERVAL,
    CONF_NAME, CONF_UNIT_OF_MEASUREMENT)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

REQUIREMENTS = ['smbus-cffi==0.5.1']
_LOGGER = logging.getLogger(__name__)

CONF_I2C_ADDRESS = 'i2c_address'
CONF_I2C_BUS = 'i2c_bus'

DEFAULT_NAME = 'MCP9808 Sensor'
DEFAULT_I2C_ADDRESS = '0x18'
DEFAULT_I2C_BUS = 1

SCAN_INTERVAL = timedelta(minutes=1)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_I2C_BUS, default=DEFAULT_I2C_BUS): vol.Coerce(int),
    vol.Optional(CONF_I2C_ADDRESS, default=DEFAULT_I2C_ADDRESS): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_UNIT_OF_MEASUREMENT): cv.string,
})


async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):
   
    """Set up the MCP number sensor."""
    name = config.get(CONF_NAME)
    unit = config.get(CONF_UNIT_OF_MEASUREMENT)
    i2c_address = config.get(CONF_I2C_ADDRESS)
    i2c_bus = config.get(CONF_I2C_BUS)
    scan_interval = config.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL)

    async_add_entities([MCP9808Sensor(name, i2c_address, i2c_bus, unit, scan_interval)], True)


class MCP9808Sensor(Entity):
    """Representation of a MCP number sensor."""

    def __init__(self, name, i2c_address, i2c_bus, unit_of_measurement, scan_interval):
        """Initialize the MCP sensor."""
        self._name = name
        self._i2c_bus = i2c_bus
        self._i2c_address = i2c_address
        self._unit_of_measurement = unit_of_measurement
        self._state = None
        self._scan_interval = scan_interval

    @property
    def name(self):
        """Return the name of the device."""
        return self._name
 
    @property
    def i2c_bus(self):
        """Return the bus of the device."""
        return self._i2c_bus
    
    @property
    def i2c_address(self):
        """Return the bus of the device."""
        return self._i2c_address

    @property
    def state(self):
        """Return the state of the device."""
        return self._state


    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return self._unit_of_measurement


    async def async_update(self):
        """Get a new number and updates the states."""
        # print(self.i2c_bus, self.i2c_address)
        bus = smbus.SMBus(self.i2c_bus) 
        v = bus.read_word_data(0x18, 0x05)
        hiByte = v & 0x00FF  # SMBus with reversed byte order
        loByte = (v >> 8) & 0x00FF
        hiByte = hiByte  & 0x1F # clear flag bit
        if hiByte & 0x10 == 0x10:  # temp < 0
            hiByte = hiByte & 0x0F  # clear sign
            temp = 256 - hiByte * 16 + loByte / 16.0 # scale
        else:
            temp = hiByte * 16 + loByte / 16.0 # scale
        temp = round(temp, 2)
        print('MCP9808 sensor Temperature: ' , temp)
        self._state = temp