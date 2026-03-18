import logging
from getpass import getpass
from pathlib import Path
import socket
from typing import Optional

from fabric import Connection
import paramiko

from experiment.ssh import HostInfo, ConnectionFactory


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


class PrivateKeyConnectionFactory(ConnectionFactory):
    def __init__(self, ssh_key: Path):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._ssh_key = ssh_key
        self._cache: dict[HostInfo, Optional[str]] = {}

    def register_ssh_connection(self, host_info: HostInfo) -> None:
        if host_info in self._cache:
            return

        if self._can_authenticate(host_info):
            self._logger.debug("can authenticate to: %s",f"{host_info.user}@{host_info.host_name}")
            self._cache[host_info] = None
            return

        passphrase = getpass(f'SSH passphrase for {self._ssh_key}: ')
        self._cache[host_info] = passphrase

    def _can_authenticate(self, host_info: HostInfo, port=22):
        with socket.create_connection((host_info.host_name, port), timeout=5) as sock:
            with paramiko.Transport(sock) as transport:
                transport.start_client(timeout=5)

                agent = paramiko.Agent()
                try:
                    agent_keys = agent.get_keys()
                    for key in agent_keys:
                        try:
                            transport.auth_publickey(host_info.user, key)
                            return True
                        except paramiko.ssh_exception.AuthenticationException:
                            pass
                finally:
                    agent.close()

                try:
                    key = paramiko.RSAKey.from_private_key_file(str(self._ssh_key))
                    transport.auth_publickey(host_info.user, key)
                    return True
                except paramiko.ssh_exception.AuthenticationException:
                    return False

    def create_connection(self, host_info: HostInfo) -> Connection:
        connect_kwargs = {
            "key_filename": str(self._ssh_key)
        }
        if self._cache[host_info] is not None:
            connect_kwargs["passphrase"] = self._cache[host_info]

        return Connection(host_info.host_name, user=host_info.user, connect_kwargs=connect_kwargs)
