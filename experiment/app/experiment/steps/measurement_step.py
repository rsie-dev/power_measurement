import logging
from contextlib import ExitStack
from pathlib import Path
from concurrent.futures import Executor
from dataclasses import dataclass

from fabric import Connection

from app.api import Command
from app.common import SSHHost
from app.experiment.base import ExperimentEnvironment
from app.experiment.base import ExperimentResources
from app.experiment.steps.measurement import measure, Measurement
from app.experiment.log import LogProvider
from .host_command_step import BaseHostCommandStep


class MeasurementStep(BaseHostCommandStep):
    @dataclass(frozen=True)
    class CommandConfig:
        runs: int
        commands: list[Command]
        tag: str

    @dataclass(frozen=True)
    class Context:
        runs: int
        commands: list[Command]
        tag: str
        log_providers: list[LogProvider]
        measurements: list[Measurement]

    def __init__(self, host: SSHHost, command_config: CommandConfig, log_providers: list[LogProvider],
                 measurements: list[Measurement]):
        super().__init__("measurement", host)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._context = MeasurementStep.Context(runs=command_config.runs, commands=command_config.commands,
                                                tag=command_config.tag,
                                                log_providers=log_providers, measurements=measurements)
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
        resources_path = self._resources_path / self._host.host_name / self._context.tag
        resources_path.mkdir(parents=True, exist_ok=True)

        tag = f"{self._context.tag} " if self._context.tag else ""
        self._logger.info("Measure %son host: %s", tag, self._host.host)

        with ExitStack() as step_stack:
            for measurement in self._context.measurements:
                step_stack.enter_context(measure(measurement, self._environment, self._executor))
            for run in range(self._context.runs):
                self._execute_run(run, resources_path, connection)

        self._logger.info("All commands measured")

    def _execute_run(self, run: int, resources_path: Path, connection: Connection):
        self._logger.info("Run %d/%d", run + 1, self._context.runs)
        run_resources_path = resources_path / ("run_%03d" % (run + 1))
        run_resources_path.mkdir(parents=True, exist_ok=True)

        with ExitStack() as run_stack:
            for log_provider in self._context.log_providers:
                run_stack.enter_context(log_provider.start_log(run_resources_path))

            timings_resources_path = run_resources_path / "timings.csv"
            for command in self._context.commands:
                command.execute(connection, timings_resources_path)
