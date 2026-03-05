from app.system_meter.metrics import SystemMeasurement
from app.system_meter.measurement_logger import MeasurementLogger


class MeasurementDispatcher(MeasurementLogger):
    def __init__(self):
        super().__init__()
        self._logger_dict: dict[str, list[MeasurementLogger]] = {}
        self._initialized = False

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, type, value, traceback):  # pylint: disable=redefined-builtin
        self.close()

    def add_logger(self, host: str, logger: MeasurementLogger) -> None:
        logger_list = self._logger_dict.get(host, [])
        logger_list.append(logger)
        self._logger_dict[host] = logger_list

    def remove_logger(self, host: str, logger: MeasurementLogger):
        logger_list = self._logger_dict.get(host, [])
        logger_list.remove(logger)
        self._logger_dict[host] = logger_list
        return logger

    def init(self) -> None:
        if self._initialized:
            return
        self._initialized = True

    def close(self):
        self._logger_dict.clear()

    def log(self, measurement: SystemMeasurement) -> None:
        host = measurement.tags["host"]
        logger_list = self._logger_dict.get(host, [])
        for logger in logger_list[:]:
            logger.log(measurement)
