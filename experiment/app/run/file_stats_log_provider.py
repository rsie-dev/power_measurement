from pathlib import Path
from typing import ContextManager
from contextlib import contextmanager

from app.experiment.steps import LogProvider
from app.experiment.log import logger, CSVFileStatLogger

from .file_stats_dispatcher import FileStatsDispatcher


class FileStatsLogProvider(LogProvider):
    def __init__(self, log_dispatcher: FileStatsDispatcher, formatter):
        self._log_dispatcher = log_dispatcher
        self._formatter = formatter

    @contextmanager
    def start_log(self, resource_path: Path) -> ContextManager:
        file_stats_log = resource_path / "file_stats.csv"

        with logger(CSVFileStatLogger(file_stats_log, self._formatter)) as data_logger:
            self._log_dispatcher.register_logger(data_logger)
            try:
                yield data_logger
            finally:
                self._log_dispatcher.unregister_logger(data_logger)
