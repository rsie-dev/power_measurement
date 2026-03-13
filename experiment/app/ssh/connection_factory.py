from abc import ABC, abstractmethod
from getpass import getpass

from fabric import Connection

from .host_info import HostInfo


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
        self._cache[host_info] = password

    def create_connection(self, host_info: HostInfo) -> Connection:
        connect_kwargs = {
            "password": self._cache[host_info],
        }
        return Connection(host_info.host_name, user=host_info.user, connect_kwargs=connect_kwargs)
