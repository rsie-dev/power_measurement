from abc import ABC, abstractmethod


class MeasurementAbort(ABC):
    def abort_measurement(self) -> bool:
        return self.get_abort_reason() is not None

    @abstractmethod
    def get_abort_reason(self) -> Exception | None:
        pass
