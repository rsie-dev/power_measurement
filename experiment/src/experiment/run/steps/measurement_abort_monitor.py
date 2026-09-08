import logging

from .measurement_abort import MeasurementAbort


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
