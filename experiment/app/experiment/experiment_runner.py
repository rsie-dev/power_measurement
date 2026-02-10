import logging
from pathlib import Path
from concurrent.futures import Executor
from typing import List

from app.common import SignalHandler
from .steps import Step
from .steps.experiment_environment import ExperimentEnvironment
from .steps.experiment_runtime import ExperimentRuntime
from .steps.experiment_measurement import ExperimentMeasurement
from .steps.experiment_resources import ExperimentResources
from .measurement import Measurement
from .resources import Resources
from .measurement_dispatcher import MeasurementDispatcher


class ExperimentRunner:
    def __init__(self, resource_path: Path, signal_handler: SignalHandler, steps: List[Step], runs):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._resource_path = resource_path
        self._signal_handler = signal_handler
        self._steps = steps[:]
        self._runs = runs

    def execute_runs(self, measurement_dispatcher: MeasurementDispatcher, executor: Executor,
                     runtime: ExperimentRuntime, environment: ExperimentEnvironment):
        for run in range(self._runs):
            self._logger.info("Start run %d/%d", run + 1, self._runs)
            run_resource = self._resource_path / ("run_%03d" % (run + 1))
            run_resource.mkdir(parents=True, exist_ok=True)
            resources = Resources(run_resource)
            measurement = Measurement(measurement_dispatcher, resources)
            self._run_experiment(environment, runtime, measurement, resources, executor)

    def _run_experiment(self, environment: ExperimentEnvironment, runtime: ExperimentRuntime,
                        measurement: ExperimentMeasurement, resources: ExperimentResources,
                        executor: Executor):
        self._logger.info("Initialize all steps")
        for step in self._steps:
            self._logger.debug("init step: %s", step.name)
            step.init(environment, measurement, resources)

        try:
            self._logger.info("Starting all steps")
            for step in self._steps:
                self._logger.debug("start step: %s", step.name)
                step.start(executor)

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
