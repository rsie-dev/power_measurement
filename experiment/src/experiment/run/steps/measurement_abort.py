import logging
from abc import ABC, abstractmethod


class MeasurementAbort(ABC):
    @abstractmethod
    def abort_measurement(self) -> bool:
        pass


class MeasurementAbortMonitor(MeasurementAbort):
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._aborter: list[MeasurementAbort] = []

    def add_aborter(self, aborter: MeasurementAbort) -> None:
        self._aborter.append(aborter)

    def abort_measurement(self) -> bool:
        for aborter in self._aborter:
            if aborter.abort_measurement():
                return True
        return False
