from .steps.experiment_measurement import ExperimentMeasurement
from .measurement_dispatcher import MeasurementDispatcher
from .steps.csv_system_logger import CSVSystemLogger
from .steps.experiment_resources import ExperimentResources


class Measurement(ExperimentMeasurement):
    def __init__(self, measurement_dispatcher: MeasurementDispatcher, resources: ExperimentResources):
        self._measurement_dispatcher = measurement_dispatcher
        self._resources = resources

    def register_for_system_meter(self, host: str) -> None:
        metric_file_path = self._resources.metrics_resources_path()
        self._measurement_dispatcher.add_logger(host, CSVSystemLogger(metric_file_path))

    def unregister_for_system_meter(self, host: str) -> None:
        logger = self._measurement_dispatcher.remove_logger(host)
        if logger:
            logger.close()
