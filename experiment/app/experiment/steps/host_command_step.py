import logging
from abc import abstractmethod
from contextlib import ExitStack

from fabric import Connection

from app.api import Command
from .step import Step
from .log_provider import LogProvider
from .host import SSHHost
from .experiment_environment import ExperimentEnvironment
from .experiment_runtime import ExperimentRuntime
from .experiment_resources import ExperimentResources


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


class HostCommandStep(BaseHostCommandStep):
    def __init__(self, host: SSHHost, runs: int, commands: list[Command], log_providers: list[LogProvider]):
        super().__init__("host command", host)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._runs = runs
        self._commands: list[Command] = commands
        self._log_providers = log_providers
        self._resources_path = None

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources):
        super().prepare(environment, resources)
        self._resources_path = resources.resources_path()

    def _execute_commands(self, connection: Connection):
        self._logger.info("on host: %s execute %d command(s)", self._host.host, len(self._commands))

        resources_path = self._resources_path / self._host.host_name
        resources_path.mkdir(parents=True, exist_ok=True)

        for run in range(self._runs):
            self._logger.info("Start run %d/%d", run + 1, self._runs)
            run_resources_path = resources_path / ("run_%03d" % (run + 1))
            run_resources_path.mkdir(parents=True, exist_ok=True)

            with ExitStack() as stack:
                for log_provider in self._log_providers:
                    stack.enter_context(log_provider.start_log(run_resources_path))

                timings_resources_path = run_resources_path / "timings.csv"
                for command in self._commands:
                    command.execute(connection, timings_resources_path)

        self._logger.info("commands executed")
