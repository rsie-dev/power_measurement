from pathlib import Path
from typing import ContextManager
from contextlib import contextmanager

from app.experiment.steps import LogProvider
from app.experiment.log import logger, LogDispatcher
from app.experiment.log import CSVMetricsLogger, MetricType
from app.system_meter import SystemMeasurement


class MetricsLogProvider(LogProvider):
    def __init__(self, log_dispatcher: LogDispatcher[SystemMeasurement], formatter, metric_type: MetricType):
        self._log_dispatcher = log_dispatcher
        self._formatter = formatter
        self._metric_type = metric_type

    @contextmanager
    def start_log(self, resource_path: Path) -> ContextManager:
        metrics_log = self._get_logfile_name(resource_path)

        with logger(CSVMetricsLogger(metrics_log, self._formatter, self._metric_type)) as data_logger:
            self._log_dispatcher.register_logger(data_logger)
            try:
                yield data_logger
            finally:
                self._log_dispatcher.unregister_logger(data_logger)

    def _get_logfile_name(self, resource_path):
        if self._metric_type == MetricType.SYSTEM:
            return resource_path / "system.csv"
        if self._metric_type == MetricType.CPU:
            return resource_path / "cpu.csv"
        raise ValueError(self._metric_type)
