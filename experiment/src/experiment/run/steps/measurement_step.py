import logging
from contextlib import ExitStack
from pathlib import Path
from concurrent.futures import Executor
from dataclasses import dataclass

from fabric import Connection

from experiment.api import Command
from experiment.common import SSHHost
from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentResources
from experiment.run.steps.measurement import measure, Measurement
from experiment.run.log import LogProvider
from .host_command_step import BaseHostCommandStep


class MeasurementStep(BaseHostCommandStep):
    @dataclass(frozen=True)
    class CommandConfig:
        runs: int
        commands: list[Command]
        tag: str
        log_providers: list[LogProvider]

    def __init__(self, host: SSHHost, measurements: list[Measurement], command_config: CommandConfig):
        super().__init__("measurement", host)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config = command_config
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
        resources_path = self._resources_path / self._host.host_name / self._config.tag
        resources_path.mkdir(parents=True, exist_ok=True)

        with ExitStack() as step_stack:
            for measurement in self._measurements:
                step_stack.enter_context(measure(measurement, self._environment, self._executor))
            for run in range(self._config.runs):
                self._execute_run(run, resources_path, connection)

    def _execute_run(self, run: int, resources_path: Path, connection: Connection):
        tag = f"{self._config.tag} " if self._config.tag else ""
        self._logger.info("Run %s%d/%d", tag, run + 1, self._config.runs)
        run_resources_path = resources_path / ("run_%03d" % (run + 1))
        run_resources_path.mkdir(parents=True, exist_ok=True)

        with ExitStack() as run_stack:
            for log_provider in self._config.log_providers:
                run_stack.enter_context(log_provider.start_log(run_resources_path))

            timings_resources_path = run_resources_path / "timings.csv"
            for i, command in enumerate(self._config.commands):
                command.execute(i + 1, connection, timings_resources_path)
