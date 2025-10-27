import csv
from pathlib import Path

from server.measurement_logger import MeasurementLogger
from server.metrics import SystemMeasurement


class CSVDataLogger(MeasurementLogger):
    FIELD_NAMES = ["timestamp", "rel time", "host", "name", "entity",
                   "load1", "load5", "load15",
                   "usage_idle", "usage_system", "usage_user", "usage_nice", "usage_iowait",
                   "usage_guest", "usage_guest_nice", "usage_irq", "usage_softirq", "usage_steal",
                   ]

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

    def log(self, measurement: SystemMeasurement) -> None:
        if self._start_time is None:
            self._start_time = measurement.timestamp
        rel_time = measurement.timestamp - self._start_time

        entry = {
            "timestamp": f"{measurement.timestamp.isoformat(timespec="milliseconds")}",
            "rel time": f"{rel_time.total_seconds():7.2f}",
            "host": f"{measurement.tags["host"]}",
            "name": f"{measurement.name}",
        }
        if measurement.name == "system":
            entry |= {
                "load1": f"{measurement.fields.load1:5.2f}",
                "load5": f"{measurement.fields.load5:5.2f}",
                "load15": f"{measurement.fields.load15:5.2f}",
            }
        elif measurement.name == "cpu":
            entry |= {
                "entity": measurement.tags["cpu"],
                "usage_guest": f"{measurement.fields.usage_guest:7.2f}",
                "usage_guest_nice": f"{measurement.fields.usage_guest_nice:7.2f}",
                "usage_idle": f"{measurement.fields.usage_idle:7.2f}",
                "usage_iowait": f"{measurement.fields.usage_iowait:7.2f}",
                "usage_irq": f"{measurement.fields.usage_irq:7.2f}",
                "usage_nice": f"{measurement.fields.usage_nice:7.2f}",
                "usage_softirq": f"{measurement.fields.usage_softirq:7.2f}",
                "usage_steal": f"{measurement.fields.usage_steal:7.2f}",
                "usage_system": f"{measurement.fields.usage_system:7.2f}",
                "usage_user": f"{measurement.fields.usage_user:7.2f}",
            }

        self._writer.writerow(entry)
