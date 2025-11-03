import logging
from getpass import getpass


class SSHManager:
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def get_password(self, user: str, host: str) -> str:
        return getpass(f'SSH password for {user}@{host}: ')

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):  # pylint: disable=redefined-builtin
        pass
