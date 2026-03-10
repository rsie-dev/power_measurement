from app.system_meter import SystemMeasurement
from app.experiment.log import Logger, LogDispatcher
from .steps.experiment_measurement import ExperimentMeasurement


class Measurement(ExperimentMeasurement):
    def __init__(self, measurement_dispatcher: LogDispatcher[SystemMeasurement]):
        self._measurement_dispatcher = measurement_dispatcher

    def register_for_system_meter(self, host: str, logger: Logger[SystemMeasurement]) -> None:
        self._measurement_dispatcher.register_logger(logger)

    def unregister_for_system_meter(self, host: str, logger: Logger[SystemMeasurement]) -> None:
        self._measurement_dispatcher.unregister_logger(logger)
