from abc import ABC, abstractmethod

from app.system_meter.measurement_logger import MeasurementLogger


class ExperimentMeasurement(ABC):
    @abstractmethod
    def register_for_system_meter(self, host: str, logger: MeasurementLogger) -> None:
        pass

    @abstractmethod
    def unregister_for_system_meter(self, host: str, logger: MeasurementLogger) -> None:
        pass
