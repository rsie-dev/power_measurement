from abc import ABC, abstractmethod
from concurrent.futures import Executor

from experiment.run.base import ExperimentEnvironment


class Measurement(ABC):
    """A per step measurement."""

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
