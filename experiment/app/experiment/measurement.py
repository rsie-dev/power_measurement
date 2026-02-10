from pathlib import Path

from .steps.experiment_measurement import ExperimentMeasurement
from .measurement_dispatcher import MeasurementDispatcher
from .steps.csv_system_logger import CSVSystemLogger


class Measurement(ExperimentMeasurement):
    def __init__(self, measurement_dispatcher: MeasurementDispatcher, resource_path: Path):
        self._measurement_dispatcher = measurement_dispatcher
        self._resource_path = resource_path

    def register_for_system_meter(self, host: str) -> None:
        metric_file_path = self._resource_path / "system.csv"
        self._measurement_dispatcher.add_logger(host, CSVSystemLogger(metric_file_path))

    def unregister_for_system_meter(self, host: str) -> None:
        logger = self._measurement_dispatcher.remove_logger(host)
        if logger:
            logger.close()
