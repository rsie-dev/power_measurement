import logging
from pathlib import Path
import time
import datetime

from experiment.run.log import CSVTemperatureLogger, TemperatureEntry
from experiment.sensor import get_sensor_device, SensorDevice
from experiment.run.log import logger


class TemperatureLogger:
    def __init__(self, log_filename: Path, formatter_info: tuple[type, dict], bus:str):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._log_filename = log_filename
        self._formatter_info = formatter_info
        self._bus = bus

    def log(self) -> None:
        formatter_class, formatter_config = self._formatter_info
        formatter = formatter_class(**formatter_config)
        self._logger.info("Log temperature readings to: %s", self._log_filename.relative_to(Path().absolute()))
        temperature_logger = CSVTemperatureLogger(self._log_filename, formatter)
        with logger(temperature_logger) as temp_logger:
            with get_sensor_device(self._bus) as sensor_device:
                self._log_loop(temp_logger, sensor_device)

    def _log_loop(self, temp_logger: CSVTemperatureLogger, sensor_device: SensorDevice) -> None:
        max_update_interval = sensor_device.get_max_update_interval()
        interval = 1 / max_update_interval
        next_run = time.monotonic()

        while True:
            temperature = sensor_device.get_temperature()
            timestamp = datetime.datetime.now(datetime.timezone.utc)
            te = TemperatureEntry(
                timestamp=timestamp,
                temperature=temperature,
            )
            temp_logger.log(te)
            self._logger.debug("current temp: %.02f °C", temperature)

            next_run += interval
            remaining = max(0, next_run - time.monotonic())

            time.sleep(remaining)
