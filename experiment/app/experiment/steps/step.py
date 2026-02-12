from abc import ABC
from concurrent.futures import Executor

from .experiment_environment import ExperimentEnvironment, InitEnvironment
from .experiment_runtime import ExperimentRuntime
from .experiment_measurement import ExperimentMeasurement
from .experiment_resources import ExperimentResources


class BaseStep(ABC):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    def execute(self, runtime: ExperimentRuntime) -> None:
        pass


class InitStep(BaseStep):
    def init(self, environment: InitEnvironment) -> None:
        pass


class Step(BaseStep):

    def prepare(self, environment: ExperimentEnvironment, measurement: ExperimentMeasurement,
                resources: ExperimentResources) -> None:
        pass

    def start(self, executor: Executor) -> None:
        pass

    def stop(self, runtime: ExperimentRuntime, measurement: ExperimentMeasurement) -> None:
        pass
