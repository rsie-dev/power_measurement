from pathlib import Path
from typing import List
import logging

from usb_multimeter import ElectricalMeasurement

from .csv_base_logger import CSVBaseLogger
from .logger import Logger


class CSVMultimeterLogger(CSVBaseLogger, Logger[ElectricalMeasurement]):
    FIELD_NAMES = ["timestamp", "temperature", "voltage", "current"]

    def __init__(self, path: Path, formatter: logging.Formatter, latest_only: bool = False):
        super().__init__(formatter, path, self.FIELD_NAMES)
        self._latest_only = latest_only

    def init(self) -> None:
        self._writer.writeheader()
        entry = {
            "timestamp": "No Unit",
            "temperature": "celsius",
            "voltage": "volt",
            "current": "ampere",
        }
        self._writer.writerow(entry)

    def _log_measurement(self, data: ElectricalMeasurement) -> None:
        formatted_time = self._format_time(data.timestamp)

        entry = {
            "timestamp": f"{formatted_time}",
            "temperature": f"{data.temperature:2.2f}",
            "voltage": f"{data.voltage:7.5f}",
            "current": f"{data.current:7.5f}",
        }
        self._writer.writerow(entry)

    def log(self, data: List[ElectricalMeasurement]) -> None:
        if self._latest_only:
            self._log_measurement(data[-1])
        else:
            for measurement in data:
                self._log_measurement(measurement)
