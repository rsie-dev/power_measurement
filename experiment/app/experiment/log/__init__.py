from contextlib import contextmanager

from .csv_electrical_logger import CSVElectricLogger
from .csv_metrics_logger import MetricType, CSVMetricsLogger
from .logger_base import LoggerBase

__all__ = [
    "LoggerBase",
    "CSVElectricLogger",
    "MetricType", "CSVMetricsLogger",
    "logger",
]


@contextmanager
def logger(logger_base: LoggerBase):
    logger_base.init()
    try:
        yield logger_base
    finally:
        logger_base.close()
