"""
Support for MNGL gas bill data from MNGL portal.

configuration.yaml

sensor:
  - platform: mngl
    mngl_dp_id: 
    scan_interval: 30
"""
import logging
from datetime import timedelta
import voluptuous as vol
import requests
import json
import time
from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.const import ( CONF_RESOURCES  )
from homeassistant.util import Throttle
from homeassistant.helpers.entity import Entity
from bs4 import BeautifulSoup

_LOGGER = logging.getLogger(__name__)

CONF_DPID = "mngl_dp_id"


BASE_URL = 'https://www.mngl.in/onlinebill/payment/ajax_load_bp_info'
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

SENSOR_PREFIX = 'mngl_'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_DPID): cv.string,
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the MNGL Energy bill sensor."""
    bp_id = config.get(CONF_DPID)

    try:
        data = MNGLBillData(bp_id)
    except RunTimeError:
        _LOGGER.error("Unable to connect to Mahadiscom Portal %s:%s",
                      BASE_URL)
        return False

    entities = []
    entities.append(MNGLBillSensor(data, "billno",))
    entities.append(MNGLBillSensor(data, "amount"))
    entities.append(MNGLBillSensor(data, "billdate"))
    entities.append(MNGLBillSensor(data, "dueDate"))
    entities.append(MNGLBillSensor(data, "billduedate"))
    add_entities(entities)


# pylint: disable=abstract-method
class MNGLBillData(object):
    """Representation of a Mahadiscom Energy Bill."""

    def __init__(self, bp_id):
        """Initialize the portal."""
        self.consumer_details = { 'bp_no': bp_id }

        self.data = None


    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update the data from the portal."""
        headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}
        try:
            response = requests.post(BASE_URL, headers=headers, data=self.consumer_details, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text,"lxml")
                self.data = soup
        except requests.ConnectionError as e:
            print("OOPS!! Connection Error. Make sure you are connected to Internet. Technical Details given below.\n")
            print(str(e))
        except requests.Timeout as e:
            print("OOPS!! Timeout Error")
            print(str(e))
        except requests.RequestException as e:
            print("OOPS!! General Error")
            print(str(e))
        except KeyboardInterrupt:
            print("Someone closed the program")    


class MNGLBillSensor(Entity):
    """Representation of a MahadiscomEnergyBill sensor."""

    def __init__(self, data, sensor_type):
        """Initialize the sensor."""
        self.data = data
        self.type = sensor_type
        self._name = SENSOR_PREFIX + '_' +  sensor_type
        self._state = None
        self.update()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    def update(self):
        """Get the latest data and use it to update our sensor state."""
        self.data.update()
        billdetails = self.data.data
        if self.type == 'billno':
            self._state = billdetails.find('input', {'name': 'bill_no'}).get('value')
        elif self.type == 'amount':
            self._state = billdetails.find('input', {'id': 'amount'}).get('value')
        elif self.type == 'billdate':
            self._state = billdetails.find_all("label", string="Bill Date. :")[0].find_next_sibling().get('value')
        elif self.type == 'billduedate':
            self._state = billdetails.find_all("label", string="Bill Due Date. :")[0].find_next_sibling().get('value')

     
