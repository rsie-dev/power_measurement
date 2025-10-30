import logging
from getpass import getpass

from fabric import Connection


class Step:
    def __init__(self, name: str):
        self.name = name

    def execute(self):
        pass


class HostStep(Step):
    def __init__(self, host: str, host_name: str, ssh_user: str, commands):
        super().__init__("host")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host
        self._host_name = host_name
        self._ssh_user = ssh_user
        self._commands = commands

    def execute(self):
        self._logger.info("on host: %s execute: %s", self._host, ",".join(self._commands))
        password = getpass(f'SSH password for {self._ssh_user}@{self._host_name}: ')
        connect_kwargs = {
            "password": password,
        }
        with Connection(self._host_name, user=self._ssh_user, connect_kwargs=connect_kwargs) as con:
            for command in self._commands:
                con.run(command, hide=True)
        self._logger.info("commands executed")
