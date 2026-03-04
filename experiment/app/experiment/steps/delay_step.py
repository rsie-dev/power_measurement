import logging
from concurrent.futures import Executor
import time


from .step import Step

from .experiment_runtime import ExperimentRuntime
from .experiment_environment import ExperimentEnvironment
from .experiment_measurement import ExperimentMeasurement
from .experiment_resources import ExperimentResources


class DelayStep(Step):
    def __init__(self, head_delay: int, delayed_step: Step):
        super().__init__("delay")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._head_delay = head_delay
        self._delayed_step = delayed_step

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources) -> None:
        self._delayed_step.prepare(environment, resources)

    def start(self, executor: Executor, measurement: ExperimentMeasurement) -> None:
        self._delayed_step.start(executor, measurement)

    def stop(self, runtime: ExperimentRuntime, measurement: ExperimentMeasurement) -> None:
        self._delayed_step.stop(runtime, measurement)

    def execute(self, runtime: ExperimentRuntime):
        if self._head_delay:
            self._logger.info("Delay execution of %s for %ss", self._delayed_step.name, self._head_delay)
            time.sleep(self._head_delay)
        self._delayed_step.execute(runtime)
