from app.system_meter.metrics import SystemMeasurement
from app.system_meter.measurement_logger import MeasurementLogger


class MeasurementDispatcher(MeasurementLogger):
    def __init__(self):
        super().__init__()
        self._logger_dict = {}

    def add_logger(self, host: str, logger) -> None:
        self._logger_dict[host] = logger

    def remove_logger(self, host: str):
        logger = self._logger_dict.pop(host)
        return logger

    def init(self) -> None:
        for logger in self._logger_dict.values():
            logger.init()

    def close(self):
        for logger in self._logger_dict.values():
            logger.close()
        self._logger_dict.clear()

    def log(self, measurement: SystemMeasurement) -> None:
        host = measurement.tags["host"]
        logger = self._logger_dict[host]
        if logger:
            logger.log(measurement)
