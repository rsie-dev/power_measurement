import logging
from getpass import getpass
from typing import Optional
from contextlib import ExitStack
from dataclasses import dataclass
from abc import ABC, abstractmethod

from fabric import Connection


@dataclass(frozen=True)
class HostInfo:
    user: str
    host_name: str


@dataclass
class ConnectionEntry:
    host_info: HostInfo
    password: str
    connection: Optional[Connection]


class SSHManager(ABC):
    @abstractmethod
    def register_ssh_connection(self, user: str, host: str) -> None:
        pass

    @abstractmethod
    def get_ssh_connection(self, user: str, host: str) -> Connection:
        pass


class SSHConnectionManager(ExitStack, SSHManager):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._connections: dict[HostInfo, ConnectionEntry] = {}

    def register_ssh_connection(self, user: str, host: str) -> None:
        host_info = HostInfo(user, host)
        if host_info in self._connections:
            return
        password = getpass(f'SSH password for {user}@{host}: ')
        entry = ConnectionEntry(host_info=host_info, password=password, connection=None)
        self._connections[host_info] = entry

    def _create_connection(self, entry: ConnectionEntry) -> Connection:
        connect_kwargs = {
            "password": entry.password,
        }
        return Connection(entry.host_info.host_name, user=entry.host_info.user, connect_kwargs=connect_kwargs)

    def get_ssh_connection(self, user: str, host: str) -> Connection:
        host_info = HostInfo(user, host)
        entry = self._connections[host_info]
        if not entry.connection:
            entry.connection = self._create_connection(entry)
            self.enter_context(entry.connection)
        return entry.connection
