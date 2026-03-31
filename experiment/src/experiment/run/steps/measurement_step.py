import logging
from contextlib import ExitStack
from pathlib import Path
from concurrent.futures import Executor
from dataclasses import dataclass

from fabric import Connection
from tqdm import tqdm

from experiment.api import Command
from experiment.common import SSHHost
from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentResources
from experiment.run.steps.measurement import measure, Measurement
from experiment.run.log import LogProvider
from .host_command_step import BaseHostCommandStep
from .log_redirect import logging_redirect_tqdm


class MeasurementStep(BaseHostCommandStep):
    @dataclass(frozen=True)
    class CommandConfig:
        run: int
        runs: int
        commands: list[Command]
        tag: str
        log_providers: list[LogProvider]

    def __init__(self, host: SSHHost, measurement: Measurement | None, command_configs: list[CommandConfig]):
        super().__init__("measurement", host)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._configs = command_configs
        self._measurement = measurement
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
        with ExitStack() as step_stack:
            if self._measurement:
                step_stack.enter_context(measure(self._measurement, self._environment, self._executor))
            self._logger.info("Taking %d measurements", len(self._configs))
            with logging_redirect_tqdm():
                bar_format = "{l_bar}{bar}| {n_fmt}/{total_fmt}"
                for command_config in tqdm(self._configs, colour="green", bar_format=bar_format):
                    resources_path = self._resources_path / self._host.host_name / command_config.tag
                    resources_path.mkdir(parents=True, exist_ok=True)
                    self._execute_run(command_config, resources_path, connection)

    def _execute_run(self, command_config: CommandConfig, resources_path: Path, connection: Connection):
        tag = f"{command_config.tag} " if command_config.tag else ""
        self._logger.info("Measure %srun %d/%d", tag, command_config.run + 1, command_config.runs)
        run_resources_path = resources_path / ("run_%03d" % (command_config.run + 1))
        run_resources_path.mkdir(parents=True, exist_ok=True)

        with ExitStack() as run_stack:
            for log_provider in command_config.log_providers:
                run_stack.enter_context(log_provider.start_log(run_resources_path))

            timings_resources_path = run_resources_path / "timings.csv"
            for i, command in enumerate(command_config.commands):
                command.execute(i + 1, connection, timings_resources_path)
