import logging
from getpass import getpass
from contextlib import ExitStack
from dataclasses import dataclass
from abc import ABC, abstractmethod

from fabric import Connection

from .ssh_manager import SSHManager


@dataclass(frozen=True)
class HostInfo:
    user: str
    host_name: str


class ConnectionFactory(ABC):
    @abstractmethod
    def register_ssh_connection(self, host_info: HostInfo) -> None:
        pass

    @abstractmethod
    def create_connection(self, host_info: HostInfo) -> Connection:
        pass


class PasswordConnectionFactory(ConnectionFactory):
    def __init__(self):
        super().__init__()
        self._cache: dict[HostInfo, str] = {}

    def register_ssh_connection(self, host_info: HostInfo) -> None:
        if host_info in self._cache:
            return
        password = getpass(f'SSH password for {host_info.user}@{host_info.host_name}: ')
        #entry = ConnectionEntry(host_info=host_info, password=password, connection=None)
        self._cache[host_info] = password

    def create_connection(self, host_info: HostInfo) -> Connection:
        connect_kwargs = {
            "password": self._cache[host_info],
        }
        return Connection(host_info.host_name, user=host_info.user, connect_kwargs=connect_kwargs)


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
