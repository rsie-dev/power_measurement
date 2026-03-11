from abc import ABC, abstractmethod
from concurrent.futures import Executor

from app.experiment.base import ExperimentEnvironment


class Measurement(ABC):
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    @abstractmethod
    def start(self, environment: ExperimentEnvironment, executor: Executor) -> None:
        pass

    @abstractmethod
    def stop(self, environment: ExperimentEnvironment) -> None:
        pass
