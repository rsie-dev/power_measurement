from abc import ABC, abstractmethod

from app.experiment.log import Logger
from app.system_meter import SystemMeasurement


class ExperimentMeasurement(ABC):
    @abstractmethod
    def register_for_system_meter(self, host: str, logger: Logger[SystemMeasurement]) -> None:
        pass

    @abstractmethod
    def unregister_for_system_meter(self, host: str, logger: Logger[SystemMeasurement]) -> None:
        pass
