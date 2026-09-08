from abc import ABC, abstractmethod


class MeasurementAbort(ABC):
    @abstractmethod
    def abort_measurement(self) -> bool:
        pass
