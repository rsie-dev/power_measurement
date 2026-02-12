from app.system_meter.measurement_logger import MeasurementLogger
from .steps.experiment_measurement import ExperimentMeasurement
from .measurement_dispatcher import MeasurementDispatcher


class Measurement(ExperimentMeasurement):
    def __init__(self, measurement_dispatcher: MeasurementDispatcher):
        self._measurement_dispatcher = measurement_dispatcher

    def register_for_system_meter(self, host: str, logger: MeasurementLogger) -> None:
        self._measurement_dispatcher.add_logger(host, logger)

    def unregister_for_system_meter(self, host: str, logger: MeasurementLogger) -> None:
        self._measurement_dispatcher.remove_logger(host, logger)
