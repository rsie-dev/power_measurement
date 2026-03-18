from abc import ABC
from concurrent.futures import Executor

from experiment.run.base import ExperimentEnvironment, InitEnvironment
from experiment.run.base import ExperimentRuntime
from experiment.run.base import ExperimentResources


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

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources) -> None:
        pass

    def start(self, executor: Executor) -> None:
        pass

    def stop(self, runtime: ExperimentRuntime) -> None:
        pass
