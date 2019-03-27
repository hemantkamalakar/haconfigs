"""Logs."""
import logging


class Logger():
    """Custom logger class."""

    def __init__(self, classname):
        """Init."""
        self.logger = logging.getLogger(__name__)
        self._class = classname

    async def debug(self, method, message):
        """Debug logger method."""
        msg = "{}({}) - {}".format(self._class, str(method), str(message))
        self.logger.debug(msg)

    async def info(self, method, message):
        """Info logger method."""
        msg = "{}({}) - {}".format(self._class, str(method), str(message))
        self.logger.info(msg)

    async def warning(self, method, message):
        """Warning logger method."""
        msg = "{}({}) - {}".format(self._class, str(method), str(message))
        self.logger.warning(msg)

    async def error(self, method, message):
        """Error logger method."""
        msg = "{}({}) - {}".format(self._class, str(method), str(message))
        self.logger.error(msg)
