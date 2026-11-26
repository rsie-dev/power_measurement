import logging
from pathlib import Path
import time
import datetime

from experiment.run.log import CSVTemperatureLogger, TemperatureEntry
from experiment.sensor import get_sensor_device, SensorDevice
from experiment.run.log import logger


class TemperatureLogger:
    def __init__(self, log_filename: Path, formatter_info: tuple[type, dict], bus:str, interval: int = 1):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._log_filename = log_filename
        self._formatter_info = formatter_info
        self._bus = bus
        self._interval = interval

    def log(self) -> None:
        formatter_class, formatter_config = self._formatter_info
        formatter = formatter_class(**formatter_config)
        self._logger.info("Log temperature readings to: %s", self._log_filename)
        log_folder = self._log_filename.parent
        log_folder.mkdir(parents=True, exist_ok=True)
        temperature_logger = CSVTemperatureLogger(self._log_filename, formatter)
        self._log_filename.parent.mkdir(parents=True, exist_ok=True)
        with logger(temperature_logger) as temp_logger:
            with get_sensor_device(self._bus) as sensor_device:
                self._log_loop(temp_logger, sensor_device)

    def _log_loop(self, temp_logger: CSVTemperatureLogger, sensor_device: SensorDevice) -> None:
        interval = self._interval
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
