import logging
from typing import Optional

from fabric import Connection

from .step import Step
from .experiment_environment import ExperimentEnvironment
from .experiment_runtime import ExperimentRuntime
from .experiment_measurement import ExperimentMeasurement
from .experiment_resources import ExperimentResources


class Command:
    def __init__(self, command: str, work_dir: Optional[str] = None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._command: str = command
        self._work_dir = work_dir

    def execute(self, connection: Connection):
        self._logger.info("execute: %s", self._command)
        work_dir = self._work_dir if self._work_dir else "."
        with connection.cd(work_dir):
            connection.run(self._command, hide=True)


class HostCommandStep(Step):
    def __init__(self,  host_name: str, ssh_user: str, commands: list[Command]):
        super().__init__("host command")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host_name = host_name
        self._ssh_user = ssh_user
        self._commands: list[Command] = commands

    def init(self, environment: ExperimentEnvironment, measurement: ExperimentMeasurement,
             resources: ExperimentResources):
        environment.register_ssh_connection(self._ssh_user, self._host_name)

    def _execute_commands(self, connection: Connection):
        self._logger.info("on host: %s execute %d command(s)", self._host_name, len(self._commands))
        for command in self._commands:
            command.execute(connection)
        self._logger.info("commands executed")

    def execute(self, runtime: ExperimentRuntime):
        connection = runtime.get_ssh_connection(self._ssh_user, self._host_name)
        self._execute_commands(connection)
