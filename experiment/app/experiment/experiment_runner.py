import logging
from pathlib import Path
from concurrent.futures import Executor
from typing import List

from app.common import SignalHandler
from app.system_meter import SystemMeasurement
from .steps import Step
from .steps.experiment_environment import ExperimentEnvironment
from .steps.experiment_runtime import ExperimentRuntime
from .measurement import Measurement
from .resources import Resources
from .log import LogDispatcher


class ExperimentRunner:
    def __init__(self, executor: Executor, resource_path: Path, signal_handler: SignalHandler, steps: List[Step]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._executor = executor
        self._resource_path = resource_path
        self._signal_handler = signal_handler
        self._steps = steps[:]

    def execute_runs(self, measurement_dispatcher: LogDispatcher[SystemMeasurement],
                     runtime: ExperimentRuntime, environment: ExperimentEnvironment):
        measurement = Measurement(measurement_dispatcher)
        resources = Resources(self._resource_path)

        self._logger.info("Prepare all steps")
        for step in self._steps:
            self._logger.debug("prepare step: %s", step.name)
            step.prepare(environment, resources)

        try:
            self._logger.info("Starting all steps")
            for step in self._steps:
                self._logger.debug("start step: %s", step.name)
                step.start(self._executor, measurement)

            try:
                with self._signal_handler.capture_signals():
                    for step in self._steps:
                        self._logger.debug("execute step: %s", step.name)
                        step.execute(runtime)
            except KeyboardInterrupt:
                pass

        finally:
            self._logger.info("Stopping all steps")
            for step in list(reversed(self._steps)):
                self._logger.debug("stop step: %s", step.name)
                step.stop(runtime, measurement)
            self._logger.info("Stopped all steps")
