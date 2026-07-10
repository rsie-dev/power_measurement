from pathlib import Path
import logging
from dataclasses import dataclass
import datetime

from .csv_base_logger import CSVBaseLogger
from .logger import Logger


@dataclass(frozen=True)
class TemperatureEntry:
    timestamp: datetime.datetime
    temperature: float


class CSVTemperatureLogger(CSVBaseLogger, Logger[TemperatureEntry]):
    FIELD_NAMES = ["timestamp", "temperature"]

    def __init__(self, path: Path, formatter: logging.Formatter, latest_only: bool = False):
        super().__init__(formatter, path, self.FIELD_NAMES)
        self._latest_only = latest_only

    def init(self) -> None:
        self._writer.writeheader()
        entry = {
            "timestamp": "No Unit",
            "temperature": "celsius",
        }
        self._writer.writerow(entry)

    def log(self, data: TemperatureEntry | list[TemperatureEntry]) -> None:
        if not isinstance(data, list):
            data = [data]

        for measurement in data:
            self._log(measurement)

    def _log(self, data: TemperatureEntry) -> None:
        formatted_time = self._format_time(data.timestamp)
        entry = {
            "timestamp": f"{formatted_time}",
            "temperature": f"{data.temperature: 3.2f}",
        }
        self._writer.writerow(entry)
