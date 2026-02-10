from concurrent.futures import Executor

from .experiment_environment import ExperimentEnvironment
from .experiment_runtime import ExperimentRuntime


class Step:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    def init(self, environment: ExperimentEnvironment) -> None:
        pass

    def start(self, executor: Executor) -> None:
        pass

    def stop(self, runtime: ExperimentRuntime) -> None:
        pass

    def execute(self, runtime: ExperimentRuntime) -> None:
        pass
