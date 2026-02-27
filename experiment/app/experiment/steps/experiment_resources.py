from abc import ABC, abstractmethod
from pathlib import Path


class ExperimentResources(ABC):
    @abstractmethod
    def resources_path(self) -> Path:
        pass
