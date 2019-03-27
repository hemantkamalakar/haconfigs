"""Logic to handle custom_components."""
import os
import re
import logging
import requests
from requests import RequestException
from pyupdate.ha_custom import common

LOGGER = logging.getLogger(__name__)


class CustomComponents():
    """Custom component class."""

    def __init__(self, base_dir, custom_repos):
        """Init."""
        self.base_dir = base_dir
        self.custom_repos = custom_repos
        self.remote_info = {}

    async def get_info_all_components(self, force=False):
        """Return all remote info if any."""
        if not force and self.remote_info:
            return self.remote_info
        remote_info = {}
        repos = await common.get_repo_data('component', self.custom_repos)
        for url in repos:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    for name, component in response.json().items():
                        try:
                            component = [
                                name,
                                component['version'],
                                await common.normalize_path(
                                    component['local_location']),
                                component['remote_location'],
                                component['visit_repo'],
                                component['changelog']
                            ]
                            remote_info[name] = component
                        except KeyError:
                            print('Could not get remote info for ' + name)
            except RequestException:
                print('Could not get remote info for ' + url)
        LOGGER.debug('get_info_all_components: %s', remote_info)
        self.remote_info = remote_info
        return remote_info

    async def get_sensor_data(self, force=False):
        """Get sensor data."""
        components = await self.get_info_all_components(force)
        cahce_data = {}
        cahce_data['domain'] = 'custom_components'
        cahce_data['has_update'] = []
        count_updateable = 0
        if components:
            for name, component in components.items():
                remote_version = component[1]
                local_file = self.base_dir + '/' + str(component[2])
                local_version = await self.get_local_version(local_file)
                has_update = (
                    remote_version and remote_version != local_version)
                not_local = (remote_version and not local_version)
                if (not not_local and remote_version):
                    if has_update and not not_local:
                        count_updateable = count_updateable + 1
                        cahce_data['has_update'].append(name)
                    cahce_data[name] = {
                        "local": local_version,
                        "remote": remote_version,
                        "has_update": has_update,
                        "not_local": not_local,
                        "repo": component[4],
                        "change_log": component[5],
                    }
        LOGGER.debug('get_sensor_data: [%s, %s]', cahce_data, count_updateable)
        return [cahce_data, count_updateable]

    async def update_all(self):
        """Update all components."""
        updates = await self.get_sensor_data()
        updates = updates[0]['has_update']
        if updates is not None:
            LOGGER.info('update_all: "%s"', updates)
            for name in updates:
                await self.upgrade_single(name)
            await self.get_info_all_components(force=True)
        else:
            LOGGER.debug('update_all: No updates avaiable.')

    async def upgrade_single(self, name):
        """Update one component."""
        LOGGER.debug('upgrade_single started: "%s"', name)
        remote_info = await self.get_info_all_components()
        remote_info = remote_info[name]
        remote_file = remote_info[3]
        local_file = self.base_dir + '/' + str(remote_info[2])
        await common.download_file(local_file, remote_file)
        await self.update_requirements(local_file)
        LOGGER.info('upgrade_single finished: "%s"', name)

    async def install(self, name):
        """Install single component."""
        sdata = await self.get_sensor_data()
        if name in sdata[0]:
            if '.' in name:
                component = str(name).split('.')[0]
                path = self.base_dir + '/custom_components/' + component
                if not os.path.isdir(path):
                    os.mkdir(path)
            await self.upgrade_single(name)

    async def get_local_version(self, path):
        """Return the local version if any."""
        return_value = ''
        if os.path.isfile(path):
            with open(path, 'r') as local:
                ret = re.compile(
                    r"^\b(VERSION|__version__)\s*=\s*['\"](.*)['\"]")
                for line in local.readlines():
                    matcher = ret.match(line)
                    if matcher:
                        return_value = str(matcher.group(2))
        return return_value

    async def update_requirements(self, path):
        """Update the requirements for a python file."""
        requirements = None
        if os.path.isfile(path):
            with open(path, 'r') as local:
                ret = re.compile(r"^\bREQUIREMENTS\s*=\s*(.*)")
                for line in local.readlines():
                    matcher = ret.match(line)
                    if matcher:
                        val = str(matcher.group(1))
                        val = val.replace('[', '')
                        val = val.replace(']', '')
                        val = val.replace(',', ' ')
                        val = val.replace("'", "")
                        requirements = val
            local.close()
            if requirements is not None:
                for package in requirements.split(' '):
                    LOGGER.info('Upgrading %s', package)
                    await common.update(package)
