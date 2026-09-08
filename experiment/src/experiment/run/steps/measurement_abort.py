import logging
from abc import ABC, abstractmethod


class MeasurementAbort(ABC):
    def abort_measurement(self) -> bool:
        return self.get_abort_reason() is not None

    @abstractmethod
    def get_abort_reason(self) -> Exception | None:
        pass

class MeasurementAbortMonitor(MeasurementAbort):
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._aborter: list[MeasurementAbort] = []

    def add_aborter(self, aborter: MeasurementAbort) -> None:
        self._aborter.append(aborter)

    def get_abort_reason(self) -> Exception | None:
        for aborter in self._aborter:
            reason = aborter.get_abort_reason()
            if reason is not None:
                return reason
        return None
