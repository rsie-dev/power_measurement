from contextlib import contextmanager

from .csv_multimeter_logger import CSVMultimeterLogger
from .csv_metrics_logger import MetricType, CSVMetricsLogger
from .csv_timing_logger import TimingEntry, TimingLogger, CSVTimingLogger
from .csv_file_stats_logger import FileStatsEntry, FileStatsLogger, CSVFileStatLogger
from .base_logger import BaseLogger

__all__ = [
    "BaseLogger",
    "CSVMultimeterLogger",
    "MetricType", "CSVMetricsLogger",
    "CSVTimingLogger", "TimingEntry", "TimingLogger",
    "FileStatsEntry", "FileStatsLogger", "CSVFileStatLogger",
    "logger",
]


@contextmanager
def logger(logger_base: BaseLogger):
    logger_base.init()
    try:
        yield logger_base
    finally:
        logger_base.close()
