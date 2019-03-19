"""
Support for getting Energy bill  data from Mahadiscom portal.

configuration.yaml

sensor:
  - platform: mahadiscom
    ConsumerNo: 170020034907
    BuNumber: 4637
    consumerType: 2
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

_LOGGER = logging.getLogger(__name__)

CONF_CONSUMERNO = "ConsumerNo"
CONF_BUNUMBER = "BuNumber"
CONF_CONSUMERTYPE = "consumerType"


BASE_URL = 'https://wss.mahadiscom.in/wss/wss?uiActionName=postViewPayBill&IsAjax=true'
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

SENSOR_PREFIX = 'mahadiscom_'
SENSOR_TYPES = {
    'billMonth': ['Bill Month',  'mdi:calender'],
    'billAmount': ['Bill Amount',  'mdi:cash-100'],
    'consumptionUnits': ['Consumption Units', 'mdi:weather-sunny'],
    'billDate': ['Bill Date',  'mdi:calender'],
    'dueDate': ['Due Date',  'mdi:calender'],
    'promptPaymentDate': ['Prompt payment date', 'mdi:calender'],

}

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CONSUMERNO): cv.string,
    vol.Required(CONF_BUNUMBER): cv.string,
    vol.Required(CONF_CONSUMERTYPE): cv.string,
    vol.Required(CONF_RESOURCES, default=[]):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)])
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Setup the Mahadiscom Energy bill sensor."""
    consumer_no = config.get(CONF_CONSUMERNO)
    bu_number = config.get(CONF_BUNUMBER)
    consumer_type = config.get(CONF_CONSUMERTYPE)

    try:
        data = MahadiscomEnergyBillData(consumer_no, bu_number, consumer_type)
    except RunTimeError:
        _LOGGER.error("Unable to connect to Mahadiscom Portal %s:%s",
                      BASE_URL)
        return False

    entities = []
    entities.append(MahadiscomEnergyBillSensor(data, "billMonth", consumer_no))
    entities.append(MahadiscomEnergyBillSensor(data, "billAmount", consumer_no))
    entities.append(MahadiscomEnergyBillSensor(data, "consumptionUnits", consumer_no))
    entities.append(MahadiscomEnergyBillSensor(data, "billDate", consumer_no))
    entities.append(MahadiscomEnergyBillSensor(data, "dueDate", consumer_no))
    entities.append(MahadiscomEnergyBillSensor(data, "promptPaymentDate", consumer_no))
    add_entities(entities)


# pylint: disable=abstract-method
class MahadiscomEnergyBillData(object):
    """Representation of a Mahadiscom Energy Bill."""

    def __init__(self, consumer_no, bu_number, consumer_type):
        """Initialize the portal."""
        self.consumer_details = {}
        self.consumer_details['ConsumerNo'] = consumer_no
        self.consumer_details['BuNumber'] = bu_number
        self.consumer_details['consumerType'] = consumer_type
        self.data = None


    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Update the data from the portal."""
        headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}
        try:
            response = requests.post(BASE_URL, headers=headers, data=self.consumer_details, timeout=10)
            self.data = json.loads(response.text)
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


class MahadiscomEnergyBillSensor(Entity):
    """Representation of a MahadiscomEnergyBill sensor."""

    def __init__(self, data, sensor_type, consumer_no):
        """Initialize the sensor."""
        self.data = data
        self.type = sensor_type
        self._name = SENSOR_PREFIX + consumer_no + '_' +  sensor_type
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
        if (billdetails and billdetails != 'error'):
            if self.type == 'billMonth':
                self._state = billdetails['billMonth']
            elif self.type == 'billAmount':
                self._state = billdetails['billAmount']
            elif self.type == 'consumptionUnits':
                self._state = billdetails['consumptionUnits']    
            elif self.type == 'billDate':
                self._state = billdetails['billDate']
            elif self.type == 'dueDate':
                self._state = billdetails['dueDate']    
            elif self.type == 'promptPaymentDate':
                val = billdetails['promptPaymentDate'].split('(', 1)[1].split(')')[0]
                self._state = time.strftime("%d-%b-%Y", time.localtime(int(val)/1000))