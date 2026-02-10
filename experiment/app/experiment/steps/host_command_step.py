import logging

from fabric import Connection

from .step import Step
from .experiment_environment import ExperimentEnvironment
from .experiment_runtime import ExperimentRuntime
from .experiment_measurement import ExperimentMeasurement
from .experiment_resources import ExperimentResources


class HostCommandStep(Step):
    def __init__(self,  host_name: str, ssh_user: str, commands):
        super().__init__("host command")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host_name = host_name
        self._ssh_user = ssh_user
        self._commands = commands

    def init(self, environment: ExperimentEnvironment, measurement: ExperimentMeasurement,
             resources: ExperimentResources):
        environment.register_ssh_connection(self._ssh_user, self._host_name)

    def _execute_commands(self, connection: Connection):
        self._logger.info("on host: %s execute: %s", self._host_name, ",".join(self._commands))
        for command in self._commands:
            connection.run(command, hide=True)
        self._logger.info("commands executed")

    def execute(self, runtime: ExperimentRuntime):
        connection = runtime.get_ssh_connection(self._ssh_user, self._host_name)
        self._execute_commands(connection)
