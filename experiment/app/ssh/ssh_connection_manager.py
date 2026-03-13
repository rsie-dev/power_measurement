import logging
from contextlib import ExitStack

from fabric import Connection

from .ssh_manager import SSHManager
from .host_info import HostInfo
from .connection_factory import ConnectionFactory


class SSHConnectionManager(ExitStack, SSHManager):
    def __init__(self, connection_factory: ConnectionFactory):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._connection_factory = connection_factory
        self._connection_cache: dict[HostInfo, Connection] = {}

    def register_ssh_connection(self, user: str, host: str) -> None:
        host_info = HostInfo(user, host)
        self._connection_factory.register_ssh_connection(host_info)

    def get_ssh_connection(self, user: str, host: str) -> Connection:
        host_info = HostInfo(user, host)
        if host_info not in self._connection_cache:
            connection = self._connection_factory.create_connection(host_info)
            self._connection_cache[host_info] = connection
            self.enter_context(connection)
        return self._connection_cache[host_info]
