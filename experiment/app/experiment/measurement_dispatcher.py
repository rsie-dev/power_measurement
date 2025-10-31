from contextlib import ExitStack

from app.system_meter.metrics import SystemMeasurement
from app.system_meter.measurement_logger import MeasurementLogger


class MeasurementDispatcher(ExitStack, MeasurementLogger):
    def __init__(self):
        super().__init__()
        self._logger_dict = {}

    def enter_host_context(self, host, logger):
        log_context = self.enter_context(logger)
        self._logger_dict[host] = log_context
        return log_context

    def init(self) -> None:
        for logger in self._logger_dict.values():
            logger.init()

    def log(self, measurement: SystemMeasurement) -> None:
        host = measurement.tags["host"]
        logger = self._logger_dict[host]
        if logger:
            logger.log(measurement)
