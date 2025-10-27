import csv
from pathlib import Path

from server.measurement_logger import MeasurementLogger
from server.metrics import Measurement


class CSVDataLogger(MeasurementLogger):
    FIELD_NAMES = ["timestamp", "rel time"]

    def __init__(self, path: Path):
        self._stream = path.open(mode="w", encoding="utf-8")
        self._writer = csv.DictWriter(self._stream, fieldnames=self.FIELD_NAMES)
        self._start_time = None

    def __enter__(self):
        self._init()
        return self

    def __exit__(self, type, value, traceback):
        self._stream.close()

    def _init(self) -> None:
        self._writer.writeheader()

    def log(self, measurement: Measurement) -> None:
        if self._start_time is None:
            self._start_time = measurement.timestamp
        rel_time = measurement.timestamp - self._start_time

        entry = {
            "timestamp": f"{measurement.timestamp.isoformat(timespec="milliseconds")}",
            "rel time": f"{rel_time.total_seconds():7.2f}",
        #     "voltage_V": f"{data.voltage:7.5f}",
        #     "current_A": f"{data.current:7.5f}",
        #     "dp_V": f"{data.dp:5.3f}",
        #     "dn_V": f"{data.dn:5.3f}",
        #     "temp_C_ema": f"{data.temperature:6.3f}",
        #     "energy_Ws": f"{data.energy:.6f}",
        #     "capacity_As": f"{data.capacity:.6f}",
        }
        self._writer.writerow(entry)
