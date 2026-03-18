import logging
from abc import abstractmethod

from fabric import Connection

from app.api import Command
from app.common import SSHHost
from app.run.base import ExperimentEnvironment
from app.run.base import ExperimentRuntime
from app.run.base import ExperimentResources
from .step import Step


class BaseHostCommandStep(Step):
    def __init__(self, name: str, host: SSHHost):
        super().__init__(name)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources):
        environment.register_ssh_connection(self._host.ssh_user, self._host.host)

    @abstractmethod
    def _execute_commands(self, connection: Connection) -> None:
        pass

    def execute(self, runtime: ExperimentRuntime):
        connection = runtime.get_ssh_connection(self._host.ssh_user, self._host.host)
        self._execute_commands(connection)


class WarmupCommandStep(BaseHostCommandStep):
    def __init__(self, host: SSHHost, commands: list[Command]):
        super().__init__("warmup command", host)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._commands: list[Command] = commands

    def _execute_commands(self, connection: Connection):
        self._logger.info("on host: %s execute %d warmup command(s)", self._host.host, len(self._commands))

        for command in self._commands:
            command.execute(connection, None)

        self._logger.info("warmup commands executed")
