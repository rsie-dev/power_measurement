from contextlib import contextmanager

from .logger import Logger
from .log_dispatcher import LogDispatcher
from .csv_multimeter_logger import CSVMultimeterLogger
from .csv_metrics_logger import MetricType, CSVMetricsLogger
from .csv_timing_logger import TimingEntry, CSVTimingLogger
from .csv_file_stats_logger import FileStatsEntry, CSVFileStatLogger
from .base_logger import BaseLogger

__all__ = [
    "Logger", "LogDispatcher",
    "BaseLogger",
    "CSVMultimeterLogger",
    "MetricType", "CSVMetricsLogger",
    "CSVTimingLogger", "TimingEntry",
    "FileStatsEntry", "CSVFileStatLogger",
    "logger",
]


@contextmanager
def logger(logger_base: BaseLogger):
    logger_base.init()
    try:
        yield logger_base
    finally:
        logger_base.close()
