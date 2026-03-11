import logging
from abc import abstractmethod
from contextlib import ExitStack
from pathlib import Path
from concurrent.futures import Executor

from fabric import Connection

from app.api import Command
from app.experiment.measurement import Measurement
from app.experiment.base import ExperimentEnvironment
from .step import Step
from .log_provider import LogProvider
from .host import SSHHost
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
    def __init__(self, host: SSHHost, commands: list[Command], runs: int, log_providers: list[LogProvider],
                 measurements: list[Measurement]):
        super().__init__("host command", host)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._runs = runs
        self._commands: list[Command] = commands
        self._log_providers = log_providers
        self._measurements = measurements
        self._resources_path = None
        self._environment = None
        self._executor = None

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources):
        super().prepare(environment, resources)
        self._resources_path = resources.resources_path()
        self._environment = environment

    def start(self, executor: Executor) -> None:
        super().start(executor)
        self._executor = executor

    def _execute_commands(self, connection: Connection):
        resources_path = self._resources_path / self._host.host_name
        resources_path.mkdir(parents=True, exist_ok=True)

        self._logger.info("On host: %s execute %d command(s)", self._host.host, len(self._commands))

        for measurement in self._measurements:
            self._logger.info("Start measurement: %s", measurement.name)
            measurement.start(self._environment, self._executor)
        try:
            for run in range(self._runs):
                self._execute_run(run, resources_path, connection)
        finally:
            for measurement in self._measurements:
                self._logger.info("Stop measurement: %s", measurement.name)
                measurement.stop(self._environment)

        self._logger.info("All commands executed")

    def _execute_run(self, run: int, resources_path: Path, connection: Connection):
        self._logger.info("Start run %d/%d", run + 1, self._runs)
        run_resources_path = resources_path / ("run_%03d" % (run + 1))
        run_resources_path.mkdir(parents=True, exist_ok=True)

        with ExitStack() as stack:
            for log_provider in self._log_providers:
                stack.enter_context(log_provider.start_log(run_resources_path))

            timings_resources_path = run_resources_path / "timings.csv"
            for command in self._commands:
                command.execute(connection, timings_resources_path)
