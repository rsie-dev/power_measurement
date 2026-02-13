from pathlib import Path
from typing import List
import csv
import logging

from app.usb_meter.data_logger import DataLogger
from app.usb_meter.measurement import ElectricalMeasurement


class CSVElectricLogger(DataLogger):
    FIELD_NAMES = ["timestamp", "rel time", "voltage_V", "current_A"]

    def __init__(self, path: Path, formatter: logging.Formatter, latest_only: bool):
        self._stream = path.open(mode="w", encoding="utf-8")
        self._writer = csv.DictWriter(self._stream, fieldnames=self.FIELD_NAMES)
        self._start_time = None
        self._latest_only = latest_only
        self._formatter = formatter

    def __enter__(self):
        self._init()
        return self

    def __exit__(self, _type, value, traceback):
        self._stream.close()

    def _init(self) -> None:
        self._writer.writeheader()

    def _log_measurement(self, data: ElectricalMeasurement) -> None:
        if self._start_time is None:
            self._start_time = data.timestamp
        rel_time = data.timestamp - self._start_time

        timestamp = data.timestamp.timestamp()
        log_record = logging.makeLogRecord({"created": timestamp})
        formatted_time = self._formatter.formatTime(log_record)

        entry = {
            "timestamp": f"{formatted_time}",
            "rel time": f"{rel_time.total_seconds():7.2f}",
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
