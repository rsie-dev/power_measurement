import logging
from pathlib import Path
from typing import ContextManager
from contextlib import contextmanager

from app.experiment.steps import LogProvider
from app.experiment.log import logger, BaseLogger, LogDispatcher
from app.experiment.log import TimingEntry, CSVTimingLogger


class TimingLogProvider(LogProvider):
    def __init__(self, log_dispatcher: LogDispatcher[TimingEntry], formatter: logging.Formatter):
        self._log_dispatcher = log_dispatcher
        self._formatter = formatter

    @contextmanager
    def start_log(self, resource_path: Path) -> ContextManager:
        base_logger = self._create_logger(resource_path, self._formatter)
        with logger(base_logger) as data_logger:
            self._log_dispatcher.register_logger(data_logger)
            try:
                yield data_logger
            finally:
                self._log_dispatcher.unregister_logger(data_logger)

    def _create_logger(self, resource_path: Path, formatter: logging.Formatter, context: dict = None) -> BaseLogger:
        timings_log = resource_path / "timings.csv"
        return CSVTimingLogger(timings_log, formatter)
