import csv
from pathlib import Path
from enum import Enum
import logging

from experiment.system_meter.metrics import SystemMeasurement
from .base_logger import BaseLogger
from .logger import Logger


class MetricType(Enum):
    SYSTEM = 1
    CPU = 2


def _get_measuremnt_type(measurement: SystemMeasurement) -> MetricType:
    if measurement.name == "system":
        return MetricType.SYSTEM
    if measurement.name == "cpu":
        return MetricType.CPU
    raise RuntimeError("unknown measurement name: %s" % measurement.name)


class CSVMetricsLogger(BaseLogger, Logger[SystemMeasurement]):
    FIELD_NAMES = ["timestamp", "host", "name"]
    SYSTEM_FIELD_NAMES = FIELD_NAMES + ["load1", "load5", "load15"]
    CPU_FIELD_NAMES = FIELD_NAMES + ["entity",
                   "usage_idle", "usage_system", "usage_user", "usage_nice", "usage_iowait",
                   "usage_guest", "usage_guest_nice", "usage_irq", "usage_softirq", "usage_steal",
                   ]

    def __init__(self, path: Path, formatter: logging.Formatter, metric_type: MetricType):
        super().__init__(formatter)
        self._type = metric_type
        self._stream = path.open(mode="x", encoding="utf-8")
        headers = self.SYSTEM_FIELD_NAMES if self._type == MetricType.SYSTEM else self.CPU_FIELD_NAMES
        self._writer = csv.DictWriter(self._stream, fieldnames=headers)

    def init(self) -> None:
        self._writer.writeheader()
        entry = {
            "timestamp": "No Unit",
            "host": "No Unit",
            "name": "No Unit",
        }
        if self._type == MetricType.SYSTEM:
            entry = entry | {
                "load1": "No Unit",
                "load5": "No Unit",
                "load15": "No Unit",
            }
        else:
            entry = entry | {
                "entity": "No Unit",
                "usage_guest": "No Unit",
                "usage_guest_nice": "No Unit",
                "usage_idle": "No Unit",
                "usage_iowait": "No Unit",
                "usage_irq": "No Unit",
                "usage_nice": "No Unit",
                "usage_softirq": "No Unit",
                "usage_steal": "No Unit",
                "usage_system": "No Unit",
                "usage_user": "No Unit",
            }
        self._writer.writerow(entry)

    def close(self) -> None:
        self._stream.close()

    def _log(self, measurement: SystemMeasurement) -> None:
        measurement_type = _get_measuremnt_type(measurement)
        if self._type != measurement_type:
            return

        formatted_time = self._format_time(measurement.timestamp)

        entry = {
            "timestamp": f"{formatted_time}",
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

    def log(self, data: SystemMeasurement | list[SystemMeasurement]) -> None:
        if not isinstance(data, list):
            data = [data]

        for measurement in data:
            self._log(measurement)
