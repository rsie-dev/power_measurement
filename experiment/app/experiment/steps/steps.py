from concurrent.futures import Executor

from .experiment_environment import ExperimentEnvironment


class Step:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    def init(self, environment: ExperimentEnvironment):
        pass

    def start(self, executor: Executor):
        pass

    def stop(self):
        pass

    def execute(self):
        pass
