from abc import ABC, abstractmethod


class ExperimentMeasurement(ABC):
    @abstractmethod
    def register_for_system_meter(self, host: str) -> None:
        pass

    @abstractmethod
    def unregister_for_system_meter(self, host: str) -> None:
        pass
