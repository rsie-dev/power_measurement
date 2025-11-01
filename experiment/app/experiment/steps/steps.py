import logging
from getpass import getpass
from concurrent.futures import Executor

from fabric import Connection

from .experiment_environment import ExperimentEnvironment


class Step:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    def init(self, environment: ExperimentEnvironment):
        pass

    def start(self, executor: Executor):
        pass

    def stop(self):
        pass

    def execute(self):
        pass


class HostCommandStep(Step):
    def __init__(self,  host_name: str, ssh_user: str, commands):
        super().__init__("host command")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host_name = host_name
        self._ssh_user = ssh_user
        self._ssh_password = None
        self._commands = commands

    def init(self, environment: ExperimentEnvironment):
        self._ssh_password = getpass(f'SSH password for {self._ssh_user}@{self._host_name}: ')

    def execute(self):
        self._logger.info("on host: %s execute: %s", self._host_name, ",".join(self._commands))
        connect_kwargs = {
            "password": self._ssh_password,
        }
        with Connection(self._host_name, user=self._ssh_user, connect_kwargs=connect_kwargs) as con:
            for command in self._commands:
                con.run(command, hide=True)
        self._logger.info("commands executed")
