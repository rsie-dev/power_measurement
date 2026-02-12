from .steps.experiment_measurement import ExperimentMeasurement
from .measurement_dispatcher import MeasurementDispatcher
from .steps.csv_metrics_logger import CSVMetricsLogger, MetricType
from .steps.experiment_resources import ExperimentResources


class Measurement(ExperimentMeasurement):
    def __init__(self, measurement_dispatcher: MeasurementDispatcher, resources: ExperimentResources):
        self._measurement_dispatcher = measurement_dispatcher
        self._resources = resources
        self._system_logger = None
        self._cpu_logger = None

    def register_for_system_meter(self, host: str) -> None:
        metric_file_path = self._resources.metrics_resources_path()
        self._system_logger = CSVMetricsLogger(MetricType.SYSTEM, metric_file_path / "system.csv")
        self._cpu_logger = CSVMetricsLogger(MetricType.CPU, metric_file_path / "cpu.csv")
        self._measurement_dispatcher.add_logger(host, self._system_logger)
        self._measurement_dispatcher.add_logger(host, self._cpu_logger)

    def unregister_for_system_meter(self, host: str) -> None:
        if self._system_logger:
            logger = self._measurement_dispatcher.remove_logger(host, self._system_logger)
            if logger:
                logger.close()
        if self._cpu_logger:
            logger = self._measurement_dispatcher.remove_logger(host, self._cpu_logger)
            if logger:
                logger.close()
