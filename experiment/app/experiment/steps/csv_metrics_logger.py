import csv
from pathlib import Path
from enum import Enum

from app.system_meter.measurement_logger import MeasurementLogger
from app.system_meter.metrics import SystemMeasurement


class MetricType(Enum):
    SYSTEM = 1
    CPU = 2


class CSVMetricsLogger(MeasurementLogger):
    FIELD_NAMES = ["timestamp", "rel time", "host", "name"]
    SYSTEM_FIELD_NAMES = FIELD_NAMES + ["load1", "load5", "load15"]
    CPU_FIELD_NAMES = FIELD_NAMES + ["entity",
                   "usage_idle", "usage_system", "usage_user", "usage_nice", "usage_iowait",
                   "usage_guest", "usage_guest_nice", "usage_irq", "usage_softirq", "usage_steal",
                   ]

    def __init__(self, metric_type: MetricType, path: Path):
        self._type = metric_type
        self._stream = path.open(mode="w", encoding="utf-8")
        headers = self.SYSTEM_FIELD_NAMES if self._type == MetricType.SYSTEM else self.CPU_FIELD_NAMES
        self._writer = csv.DictWriter(self._stream, fieldnames=headers)
        self._start_time = None

    def init(self) -> None:
        self._writer.writeheader()

    def close(self):
        self._stream.close()

    def __enter__(self):
        self.init()
        return self

    def __exit__(self, _type, value, traceback):
        self.close()

    def log(self, measurement: SystemMeasurement) -> None:
        if self._start_time is None:
            self._start_time = measurement.timestamp
        rel_time = measurement.timestamp - self._start_time

        measurement_type = self._get_measuremnt_type(measurement)
        if self._type != measurement_type:
            return

        entry = {
            "timestamp": f"{measurement.timestamp.isoformat(timespec="milliseconds")}",
            "rel time": f"{rel_time.total_seconds():7.2f}",
            "host": f"{measurement.tags["host"]}",
            "name": f"{measurement.name}",
        }
        if measurement_type == MetricType.SYSTEM:
            entry |= {
                "load1": f"{measurement.fields.load1:5.2f}",
                "load5": f"{measurement.fields.load5:5.2f}",
                "load15": f"{measurement.fields.load15:5.2f}",
            }
        elif measurement_type == MetricType.CPU:
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

    def _get_measuremnt_type(self, measurement: SystemMeasurement) -> MetricType:
        if measurement.name == "system":
            return MetricType.SYSTEM
        elif measurement.name == "cpu":
            return MetricType.CPU
        raise RuntimeError("unknown measurement name: %s" % measurement.name)
