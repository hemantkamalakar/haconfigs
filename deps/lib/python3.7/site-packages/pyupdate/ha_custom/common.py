"""Logic to handle common functions."""
import os
import fileinput
import subprocess
import sys
import requests
from pyupdate.log import Logger

LOGGER = Logger('Common')


async def get_default_repos():
    """Return default repos."""
    git_base = 'https://raw.githubusercontent.com/'
    card = [git_base + 'custom-cards/information/master/repos.json']
    component = [git_base + 'custom-components/information/master/repos.json']
    python_script = [None]
    return {'component': component,
            'card': card,
            'python_script': python_script}


async def get_repo_data(resource, extra_repos=None):
    """Update the data about components."""
    repos = []
    default_repos = await get_default_repos()
    default_repos = default_repos[resource]
    if None not in default_repos:
        for repo in default_repos:
            repos.append(str(repo))
    if extra_repos is not None:
        for repo in extra_repos:
            if repo[-3:] == '.js':
                await LOGGER.warning(
                    'get_repo_data',
                    "Custom URL should be json, not .js - '{}'".format(repo))
                continue
            repos.append(str(repo))
    await LOGGER.debug('get_repo_data', repos)
    return repos


async def check_local_premissions(file):
    """Check premissions of a file."""
    dirpath = os.path.dirname(file)
    return os.access(dirpath, os.W_OK)


async def check_remote_access(file):
    """Check access to remote file."""
    test_remote_file = requests.get(file)
    return bool(test_remote_file.status_code == 200)


async def download_file(local_file, remote_file):
    """Download a file."""
    await LOGGER.debug(
        'download_file',
        "Downloading '{}' to '{}'".format(remote_file, local_file))
    if await check_local_premissions(local_file):
        if await check_remote_access(remote_file):
            with open(local_file, 'wb') as file:
                file.write(requests.get(remote_file).content)
            file.close()
            retrun_value = True
        else:
            await LOGGER.debug(
                'download_file',
                'Remote file not accessable. "{}"'.format(remote_file))
            retrun_value = False
    else:
        await LOGGER.debug(
            'download_file',
            'Local file not accessable. "{}"'.format(local_file))
        retrun_value = False
    return retrun_value


async def normalize_path(path):
    """Normalize the path."""
    path = path.replace('/', os.path.sep).replace('\\', os.path.sep)
    if path.startswith(os.path.sep):
        path = path[1:]
    return path


async def replace_all(file, search, replace):
    """Replace all occupancies of search in file."""
    await LOGGER.debug(
        'replace_all',
        "Replacing all '{}' with '{}' in file '{}'".format(
            search, replace, file))
    for line in fileinput.input(file, inplace=True):
        if search in line:
            line = line.replace(search, replace)
        sys.stdout.write(line)


async def update(package):
    """Update a pip package."""
    await LOGGER.debug('update', 'Starting upgrade of {}'.format(package))
    await subprocess.call(
        [sys.executable, "-m", "pip", "install", "--upgrade", package])
