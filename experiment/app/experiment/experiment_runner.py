import logging
from pathlib import Path
from concurrent.futures import Executor
from typing import List

from app.common import SignalHandler
from .steps import Step
from .steps.experiment_environment import ExperimentEnvironment
from .steps.experiment_runtime import ExperimentRuntime
from .steps.experiment_measurement import ExperimentMeasurement
from .steps import RunResourceStep
from .measurement import Measurement
from .resources import Resources
from .measurement_dispatcher import MeasurementDispatcher


class ExperimentRunner:
    def __init__(self, executor: Executor, resource_path: Path, signal_handler: SignalHandler, steps: List[Step]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._executor = executor
        self._resource_path = resource_path
        self._signal_handler = signal_handler
        self._steps = steps[:]

    def execute_runs(self, run_count: int, measurement_dispatcher: MeasurementDispatcher,
                     runtime: ExperimentRuntime, environment: ExperimentEnvironment):
        for run in range(run_count):
            self._logger.info("Start run %d/%d", run + 1, run_count)
            run_resource = self._resource_path / ("run_%03d" % (run + 1))
            run_resource.mkdir(parents=True, exist_ok=True)
            measurement = Measurement(measurement_dispatcher)
            self._execute_run(environment, runtime, measurement, run_resource)

    def _execute_run(self, environment: ExperimentEnvironment, runtime: ExperimentRuntime,
                     measurement: ExperimentMeasurement, run_resource: Path):
        resource_prefix = self._get_resource_prefix()
        if resource_prefix:
            resource_path = run_resource / resource_prefix
            resource_path.mkdir(parents=True, exist_ok=True)
        else:
            resource_path = run_resource
        resources = Resources(resource_path)

        self._logger.info("Prepare all steps")
        for step in self._steps:
            self._logger.debug("prepare step: %s", step.name)
            step.prepare(environment, measurement, resources)

        try:
            self._logger.info("Starting all steps")
            for step in self._steps:
                self._logger.debug("start step: %s", step.name)
                step.start(self._executor)

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

    def _get_resource_prefix(self):
        prefixes = []
        for step in self._steps:
            self._logger.warning("prefix check: %s", step.__class__.__name__)
            if isinstance(step, RunResourceStep):
                self._logger.warning("found prefix: %s", step.get_run_prefix())
                prefixes.append(step.get_run_prefix())
        return "".join(prefixes)
