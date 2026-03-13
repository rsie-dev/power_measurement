import logging
from getpass import getpass
from typing import Optional
from contextlib import ExitStack
from dataclasses import dataclass

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


class SSHManager(ExitStack):

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._connections: dict[str, ConnectionEntry] = {}

    def _build_entry_name(self, host_info: HostInfo) -> str:
        return f"{host_info.user}@{host_info.host_name}"

    def register_ssh_connection(self, user: str, host: str) -> None:
        host_info = HostInfo(user, host)
        entry_name = self._build_entry_name(host_info)
        if entry_name in self._connections:
            return
        password = getpass(f'SSH password for {user}@{host}: ')
        entry = ConnectionEntry(host_info=host_info, password=password, connection=None)
        self._connections[entry_name] = entry

    def _create_connection(self, entry: ConnectionEntry) -> Connection:
        connect_kwargs = {
            "password": entry.password,
        }
        return Connection(entry.host_info.host_name, user=entry.host_info.user, connect_kwargs=connect_kwargs)

    def get_ssh_connection(self, user: str, host: str) -> Connection:
        host_info = HostInfo(user, host)
        entry_name = self._build_entry_name(host_info)
        entry = self._connections[entry_name]
        if not entry.connection:
            entry.connection = self._create_connection(entry)
            self.enter_context(entry.connection)
        return entry.connection
