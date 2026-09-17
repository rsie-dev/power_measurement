import logging
from concurrent.futures import Executor
from dataclasses import dataclass
from pathlib import Path
from contextlib import ExitStack

from experiment.common import Host
from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentRuntime
from experiment.run.base import ExperimentResources
from experiment.run.log import LogProvider

from .step import Step


class HostLoggingStep(Step):
    @dataclass(frozen=True)
    class Config:
        host: Host
        log_provider: LogProvider

    @dataclass
    class RunContext:
        resources_path: Path | None = None
        logging_stack: ExitStack | None = None

    def __init__(self, config: Config):
        super().__init__("host logging")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config = config
        self._context = HostLoggingStep.RunContext()

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources) -> None:
        self._context.resources_path = resources.resources_path()

    def start(self, runtime: ExperimentRuntime, executor: Executor) -> None:
        self._logger.info("Start host logging for: %s", self._config.host.host_name)

        stack = ExitStack()
        self._context.logging_stack = stack.__enter__() # pylint: disable=unnecessary-dunder-call
        cm = self._config.log_provider.start_log(self._context.resources_path)
        self._context.logging_stack.enter_context(cm)

    def stop(self, runtime: ExperimentRuntime) -> None:
        self._logger.info("Stop host logging for: %s", self._config.host.host_name)
        self._context.logging_stack.__exit__(None, None, None)

    def execute(self, runtime: ExperimentRuntime) -> None:
        pass
