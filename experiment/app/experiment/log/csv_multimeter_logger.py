from pathlib import Path
from typing import List
import csv
import logging

from app.usb_meter.data_logger import DataLogger
from app.usb_meter.measurement import ElectricalMeasurement
from .logger_base import LoggerBase


class CSVMultimeterLogger(LoggerBase, DataLogger):
    FIELD_NAMES = ["timestamp", "rel_time_S", "temperature_C", "voltage_V", "current_A"]

    def __init__(self, path: Path, formatter: logging.Formatter, latest_only: bool):
        super().__init__(formatter)
        self._stream = path.open(mode="w", encoding="utf-8")
        self._writer = csv.DictWriter(self._stream, fieldnames=self.FIELD_NAMES)
        self._start_time = None
        self._latest_only = latest_only

    def init(self) -> None:
        self._writer.writeheader()

    def close(self) -> None:
        self._stream.close()

    def _log_measurement(self, data: ElectricalMeasurement) -> None:
        if self._start_time is None:
            self._start_time = data.timestamp
        rel_time = data.timestamp - self._start_time

        formatted_time = self._format_time(data.timestamp)

        entry = {
            "timestamp": f"{formatted_time}",
            "rel_time_S": f"{rel_time.total_seconds():8.3f}",
            "temperature_C": f"{data.temperature:2.2f}",
            "voltage_V": f"{data.voltage:7.5f}",
            "current_A": f"{data.current:7.5f}",
        }
        self._writer.writerow(entry)

    def log(self, data: List[ElectricalMeasurement]) -> None:
        if self._latest_only:
            self._log_measurement(data[-1])
        else:
            for measurement in data:
                self._log_measurement(measurement)
