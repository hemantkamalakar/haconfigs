"""Logic to handle custom_cards."""
import json
import os
from typing import IO, Any

import requests
from requests import RequestException
import yaml
from pyupdate.ha_custom import common
from pyupdate.log import Logger


class Loader(yaml.SafeLoader):
    """YAML Loader with `!include` constructor."""

    def __init__(self, stream: IO) -> None:
        """Initialise Loader."""
        try:
            self._root = os.path.split(stream.name)[0]
        except AttributeError:
            self._root = os.path.curdir

        super().__init__(stream)


def construct_include(loader: Loader, node: yaml.Node) -> Any:
    """Include file referenced at node."""
    filename = os.path.abspath(
        os.path.join(loader._root, loader.construct_scalar(node)))
    extension = os.path.splitext(filename)[1].lstrip('.')

    with open(filename, 'r') as localfile:
        if extension in ('yaml', 'yml'):
            return yaml.load(localfile, Loader)
        elif extension in ('json', ):
            return json.load(localfile)
        else:
            return ''.join(localfile.readlines())


yaml.add_constructor('!include', construct_include, Loader)


class CustomCards():
    """Custom_cards class."""

    def __init__(self, base_dir, mode, skip, custom_repos):
        """Init."""
        self.base_dir = base_dir
        self.mode = mode
        self.skip = skip
        self.log = Logger('CustomCards')
        self.local_cards = []
        self.custom_repos = custom_repos
        self.remote_info = None

    async def get_info_all_cards(self, force=False):
        """Return all remote info if any."""
        await self.log.debug('get_info_all_cards', 'Started')
        if not force and self.remote_info is not None:
            await self.log.debug('get_info_all_cards', 'Using stored data')
            return self.remote_info
        remote_info = {}
        repos = await common.get_repo_data('card', self.custom_repos)
        for url in repos:
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    for name, card in response.json().items():
                        try:
                            entry = {}
                            entry['name'] = name
                            entry['version'] = card['version']
                            entry['remote_location'] = card['remote_location']
                            entry['visit_repo'] = card['visit_repo']
                            entry['changelog'] = card['changelog']
                            remote_info[name] = entry
                        except KeyError:
                            print('Could not get remote info for ' + name)
            except RequestException:
                print('Could not get remote info for ' + url)
        self.remote_info = remote_info
        await self.log.debug(
            'get_info_all_cards', 'Updated stored data ' + str(remote_info))
        return remote_info

    async def init_local_data(self):
        """Init new version file."""
        await self.log.debug('init_local_data', 'Started')
        remote = await self.get_info_all_cards()
        if not self.local_cards:
            await self.localcards()
        for card in remote:
            version, path = None, None
            if card in self.local_cards:
                current = await self.local_data(card, 'get')
                if 'version' not in current.keys():
                    await self.log.debug(
                        'init_local_data',
                        'Setting initial version for {}'.format(card))
                    version = await self.get_remote_version(card)
                await self.log.debug(
                    'init_local_data', 'Setting path for {}'.format(card))
                path = await self.get_card_dir(card, True)

                await self.local_data(
                    name=card, action='set', version=version, localdir=path)

    async def get_sensor_data(self):
        """Get sensor data."""
        await self.log.debug('get_sensor_data', 'Started')
        if not self.local_cards:
            await self.localcards()
        cards = await self.get_info_all_cards()
        await self.log.debug(
            'get_sensor_data', 'Number of cards: ' + str(len(cards.keys())))
        await self.log.debug(
            'get_sensor_data', 'Cards: ' + str(cards.keys()))
        cahce_data = {}
        cahce_data['domain'] = 'custom_cards'
        cahce_data['has_update'] = []
        count_updateable = 0
        if cards:
            for card in cards:
                if card not in self.local_cards:
                    continue
                remote_version = cards[card]['version']
                local_version = await self.get_local_version(
                    cards[card]['name'])
                has_update = (
                    remote_version and remote_version != local_version)
                carddir = await self.get_card_dir(cards[card]['name'])
                not_local = True if carddir is None else False
                if (not not_local and remote_version):
                    if has_update and not not_local:
                        count_updateable = count_updateable + 1
                        cahce_data['has_update'].append(cards[card]['name'])
                    cahce_data[cards[card]['name']] = {
                        "local": local_version,
                        "remote": remote_version,
                        "has_update": has_update,
                        "not_local": not_local,
                        "repo": cards[card]['visit_repo'],
                        "change_log": cards[card]['changelog'],
                    }
        await self.log.debug(
            'get_sensor_data',
            'get_sensor_data: [{}, {}]'.format(cahce_data, count_updateable))
        return [cahce_data, count_updateable]

    async def update_all(self):
        """Update all cards."""
        await self.log.debug('update_all', 'Started')
        updates = await self.get_sensor_data()
        updates = updates[0]['has_update']
        if updates is not None:
            await self.log.info('update_all', updates)
            for name in updates:
                await self.upgrade_single(name)
            await self.get_info_all_cards(force=True)
        else:
            await self.log.info('update_all', 'No updates avaiable')

    async def force_reload(self):
        """Force data refresh."""
        await self.log.debug('force_reload', 'Started')
        await self.get_info_all_cards(True)
        await self.get_sensor_data()

    async def upgrade_single(self, name):
        """Update one card."""
        await self.log.info('upgrade_single', 'Started')
        remote_info = await self.get_info_all_cards()
        remote_info = remote_info[name]
        remote_file = remote_info['remote_location']
        local_file = await self.get_card_dir(name) + name + '.js'
        await common.download_file(local_file, remote_file)
        await self.upgrade_lib(name)
        await self.upgrade_editor(name)
        await self.update_resource_version(name)
        await self.log.info('upgrade_single', 'Finished ' + name)

    async def upgrade_lib(self, name):
        """Update one card-lib."""
        await self.log.debug('upgrade_lib', 'Started')
        remote_info = await self.get_info_all_cards()
        remote_info = remote_info[name]
        remote_file = remote_info['remote_location'][:-3] + '.lib.js'
        local_file = await self.get_card_dir(name) + name + '.lib.js'
        await common.download_file(local_file, remote_file)

    async def upgrade_editor(self, name):
        """Update one card-editor."""
        await self.log.debug('upgrade_editor', 'Started')
        remote_info = await self.get_info_all_cards()
        remote_info = remote_info[name]
        remote_file = remote_info['remote_location'][:-3] + '-editor.js'
        local_file = await self.get_card_dir(name) + name + '-editor.js'
        await common.download_file(local_file, remote_file)

    async def install(self, name):
        """Install single card."""
        await self.log.debug('install', 'Started')
        if name in await self.get_sensor_data()[0]:
            await self.upgrade_single(name)

    async def update_resource_version(self, name):
        """Update the ui-lovelace file."""
        await self.log.debug('update_resource_version', 'Started')
        remote_version = await self.get_info_all_cards()
        remote_version = remote_version[name]['version']
        await self.local_data(name, 'set', version=str(remote_version))

    async def get_card_dir(self, name, force=False):
        """Get card dir."""
        await self.log.debug('get_card_dir', 'Started')
        resources = {}
        card_dir = None
        stored_dir = await self.local_data(name)
        stored_dir = stored_dir.get('dir', None)
        if stored_dir is not None and not force:
            await self.log.debug(
                'get_card_dir', 'Using stored data for {}'.format(name))
            return stored_dir

        if self.mode == 'storage':
            resources = await self.storage_resources()
        else:
            resources = await self.yaml_resources()
        for entry in resources:
            if entry['url'][:4] == 'http':
                continue
            entry_name = entry['url'].split('/')[-1].split('.js')[0]
            if name == entry_name:
                card_dir = entry['url']
                break

        if card_dir is None:
            return None

        if '/customcards/' in card_dir:
            card_dir = card_dir.replace('/customcards/', '/www/')
        if '/local/' in card_dir:
            card_dir = card_dir.replace('/local/', '/www/')

        stored_dir = "{}{}".format(
            self.base_dir, card_dir).split(name + '.js')[0]
        await self.local_data(name, action='set', localdir=stored_dir)
        await self.log.debug('get_card_dir', stored_dir)
        return stored_dir

    async def get_local_version(self, name):
        """Return the local version if any."""
        await self.log.debug('get_local_version', 'Started')
        version = await self.local_data(name)
        version = version.get('version')
        await self.log.debug('get_local_version', version)
        return version

    async def get_remote_version(self, name):
        """Return the remote version if any."""
        await self.log.debug('get_remote_version', 'Started')
        version = await self.get_info_all_cards()
        version = version.get(name, {}).get('version')
        await self.log.debug('get_remote_version', version)
        return version

    async def local_data(
            self, name=None, action='get', version=None, localdir=None):
        """Write or get info from storage."""
        await self.log.debug('local_data', 'Started')
        data = {'action': action,
                'name': name,
                'version': version,
                'dir': localdir}
        await self.log.debug('local_data', data)
        returnvalue = None
        jsonfile = "{}/.storage/custom_updater.cards".format(self.base_dir)
        if os.path.isfile(jsonfile):
            with open(jsonfile) as storagefile:
                try:
                    load = json.load(storagefile)
                except Exception as error:  # pylint: disable=W0703
                    load = {}
                    await self.log.error('local_data', error)
        else:
            load = {}

        if action == 'get':
            if name is None:
                returnvalue = load
            else:
                returnvalue = load.get(name, {})
        else:
            card = load.get(name, {})
            if version is not None:
                card['version'] = version
            if localdir is not None:
                card['dir'] = localdir
            load[name] = card
            with open(jsonfile, 'w') as outfile:
                json.dump(load, outfile, indent=4)
                outfile.close()
        await self.log.debug('local_data', returnvalue)
        return returnvalue

    async def storage_resources(self):
        """Load resources from storage."""
        await self.log.debug('storage_resources', 'Started')
        resources = {}
        jsonfile = "{}/.storage/lovelace".format(self.base_dir)
        if os.path.isfile(jsonfile):
            with open(jsonfile) as localfile:
                load = json.load(localfile)
                resources = load['data']['config'].get('resources', {})
                localfile.close()
        else:
            await self.log.error(
                'storage_resources',
                'Lovelace config in .storage file not found')
        await self.log.debug('storage_resources', resources)
        return resources

    async def yaml_resources(self):
        """Load resources from yaml."""
        await self.log.debug('yaml_resources', 'Started')
        resources = {}
        yamlfile = "{}/ui-lovelace.yaml".format(self.base_dir)
        if os.path.isfile(yamlfile):
            with open(yamlfile) as localfile:
                load = yaml.load(localfile, Loader)
                resources = load.get('resources', {})
                localfile.close()
        else:
            await self.log.error(
                'yaml_resources', 'Lovelace config in yaml file not found')
        await self.log.debug('yaml_resources', resources)
        return resources

    async def localcards(self):
        """Return local cards."""
        await self.log.debug('localcards', 'Started')
        await self.log.debug(
            'localcards', 'Getting local cards with mode: ' + self.mode)
        local_cards = []
        resources = {}
        if self.mode == 'storage':
            resources = await self.storage_resources()
        else:
            resources = await self.yaml_resources()
        for entry in resources:
            if entry['url'][:4] == 'http':
                continue
            local_cards.append(entry['url'].split('/')[-1].split('.js')[0])
        self.local_cards = local_cards
        await self.log.debug('localcards', self.local_cards)
