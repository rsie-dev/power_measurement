from pathlib import Path
from typing import ContextManager
from contextlib import contextmanager

from app.experiment.steps import LogProvider
from app.experiment.log import logger, LogDispatcher
from app.experiment.log import CSVMultimeterLogger
from app.usb_meter.measurement import ElectricalMeasurement


class MultimeterLogProvider(LogProvider):
    def __init__(self, log_dispatcher: LogDispatcher[ElectricalMeasurement], formatter):
        self._log_dispatcher = log_dispatcher
        self._formatter = formatter

    @contextmanager
    def start_log(self, resource_path: Path) -> ContextManager:
        multimeter_log = resource_path / "multimeter.csv"

        with logger(CSVMultimeterLogger(multimeter_log, self._formatter)) as data_logger:
            self._log_dispatcher.register_logger(data_logger)
            try:
                yield data_logger
            finally:
                self._log_dispatcher.unregister_logger(data_logger)
