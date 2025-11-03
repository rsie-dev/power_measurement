import logging
from getpass import getpass
from typing import Optional
from contextlib import ExitStack

from fabric import Connection


class ConnectionEntry:
    def __init__(self, user: str, host_name: str, password: str):
        self.user: str = user
        self.host_name: str = host_name
        self.password: str = password
        self.connection: Optional[Connection] = None


class SSHManager(ExitStack):

    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._connections: dict[str, ConnectionEntry] = {}

    def _build_entry_name(self, user: str, host: str) -> str:
        return f"{user}@{host}"

    def register_ssh_connection(self, user: str, host: str) -> None:
        entry_name = self._build_entry_name(user, host)
        if entry_name in self._connections:
            return
        password = getpass(f'SSH password for {user}@{host}: ')
        entry = ConnectionEntry(user, host, password)
        self._connections[entry_name] = entry

    def _create_connection(self, entry: ConnectionEntry) -> Connection:
        connect_kwargs = {
            "password": entry.password,
        }
        return Connection(entry.host_name, user=entry.user, connect_kwargs=connect_kwargs)

    def get_ssh_connection(self, user: str, host: str) -> Connection:
        entry_name = self._build_entry_name(user, host)
        entry = self._connections[entry_name]
        if not entry.connection:
            entry.connection = self._create_connection(entry)
            self.enter_context(entry.connection)
        return entry.connection
