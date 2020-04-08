"""
A platform which allows you to get information about Covid-19 status in India.
For more details about this component, please refer to the documentation at
https://github.com/hemantkamalakar/Covid19IndiaTracker
"""
# pylint: disable=unused-argument,missing-docstring
from datetime import timedelta
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from integrationhelper import WebClient, Logger
from integrationhelper.const import CC_STARTUP

URL = "https://api.covid19india.org/data.json"
ISSUE_LINK = "https://github.com/hemantkamalakar/Covid19IndiaTracker/issues/"
SCAN_INTERVAL = timedelta(seconds=300)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    logger = Logger(__name__)
    logger.info(CC_STARTUP.format(name="Covid19IndiaTracker", issue_link=ISSUE_LINK))
    webclient = WebClient(async_get_clientsession(hass), logger)
    async_add_entities([Covid19IndiaTrackerSensor(webclient)], True)


class Covid19IndiaTrackerSensor(Entity):
    def __init__(self, webclient):
        self._state = None
        self._india_confirmed = None
        self._india_total_deaths = None
        self._india_total_recovered = None
        self._india_today_confirmed = None
        self._india_today_deaths = None
        self._maharashtra_confirmed = None
        self._maharashtra_total_deaths = None
        self._maharashtra_total_recovered = None
        self._maharashtra_today_confirmed = None
        self._maharashtra_today_deaths = None
        self._last_updated = None
        self.webclient = webclient

    async def async_update(self):
        Covid19IndiaTracker = await self.webclient.async_get_json(
            URL, {"Accept": "application/json"}
        )
        rbd = Covid19IndiaTracker
        for state in rbd['statewise']:
            if (state['state'] == 'Total'):
                self._state = state['confirmed']
                self._india_confirmed = state['confirmed']
                self._india_total_deaths = state['deaths']
                self._india_total_recovered = state['recovered']
                # self._india_today_confirmed = state['delta']['confirmed']
                # self._india_today_deaths = state['delta']['deaths']
                self._india_today_confirmed = state['deltaconfirmed']
                self._india_today_deaths = state['deltadeaths']
                self._last_updated = state['lastupdatedtime']
                print(state)
            elif (state['state'] == 'Maharashtra'):
                self._maharashtra_confirmed = state['confirmed']
                self._maharashtra_total_deaths = state['deaths']
                self._maharashtra_total_recovered = state['recovered']
                # self._maharashtra_today_confirmed = state['delta']['confirmed']
                # self._maharashtra_today_deaths = state['delta']['deaths']
                self._maharashtra_today_confirmed = state['deltaconfirmed']
                self._maharashtra_today_deaths = state['deltadeaths']
                print(state)

    @property
    def name(self):
        return "INDIA COVID-19 TRACKER"

    @property
    def last_updated(self):
        """Returns date when it was last updated."""
        if isinstance(self._last_updated, int):
            return self._last_updated

    @property
    def unit_of_measurement(self):
        """Returns the unit of measurement."""
        return 'cases'

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return "mdi-emoticon-devil"

    @property
    def device_state_attributes(self):
        return {
            "india_confirmed": self._india_confirmed, 
            "india_total_deaths": self._india_total_deaths, 
            "india_total_recovered": self._india_total_recovered,
            "india_today_confirmed": self._india_today_confirmed,
            "india_today_deaths": self._india_today_deaths,
            "maharashtra_confirmed": self._maharashtra_confirmed,
            "maharashtra_total_deaths": self._maharashtra_total_deaths,
            "maharashtra_total_recovered": self._maharashtra_total_recovered,
            "maharashtra_today_confirmed": self._maharashtra_today_confirmed,
            "maharashtra_today_deaths": self._maharashtra_today_deaths,
            "lastupdated": self.last_updated
            }
        
