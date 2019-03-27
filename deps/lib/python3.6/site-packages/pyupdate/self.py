"""Logic to handle pyupdate."""
import subprocess
import sys
import json
import requests


def update():
    """Update this package."""
    version = get_pypi_version()
    packageversion = 'pyupdate' + version
    subprocess.call([sys.executable,
                     "-m",
                     "pip",
                     "install",
                     "--upgrade",
                     packageversion])


def get_pypi_version():
    """Get the PyPi version of this package."""
    url = 'https://pypi.org/pypi/pyupdate/json'
    try:
        version = '==' + requests.get(url).json()['info']['version']
    except json.decoder.JSONDecodeError:
        version = ''
    return version
