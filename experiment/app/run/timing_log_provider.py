from pathlib import Path
from typing import ContextManager
from contextlib import contextmanager

from app.experiment.steps import LogProvider
from app.experiment.log import logger, CSVTimingLogger

from .timing_dispatcher import TimingDispatcher

class TimingLogProvider(LogProvider):
    def __init__(self, timing_dispatcher: TimingDispatcher, formatter):
        self._timing_dispatcher = timing_dispatcher
        self._formatter = formatter

    @contextmanager
    def start_log(self, resource_path: Path) -> ContextManager:
        timings_log = resource_path / "timings.csv"

        with logger(CSVTimingLogger(timings_log, self._formatter)) as data_logger:
            self._timing_dispatcher.register_logger(data_logger)
            try:
                yield data_logger
            finally:
                self._timing_dispatcher.unregister_logger(data_logger)
