import logging
from concurrent.futures import Executor
from typing import List

from usb_multimeter import ElectricalMeasurement

from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentRuntime
from experiment.run.base import ExperimentResources
from experiment.run.log import LogDispatcher, Logger

from .step import Step
from .measurement_step import MeasurementAbort


class TempMonitorStep(Step, Logger, MeasurementAbort):
    def __init__(self, log_dispatcher: LogDispatcher[ElectricalMeasurement], max_temp_delta: float):
        super().__init__("temperature monitor")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._log_dispatcher = log_dispatcher
        self._max_temp_delta = max_temp_delta

    def abort_measurement(self) -> bool:
        return False

    def execute(self, runtime: ExperimentRuntime) -> None:
        pass

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources) -> None:
        pass

    def start(self, executor: Executor) -> None:
        self._logger.warning("temp monitor start")
        self._log_dispatcher.register_logger(self)

    def stop(self, runtime: ExperimentRuntime) -> None:
        self._log_dispatcher.unregister_logger(self)
        self._logger.warning("temp monitor stop")

    def _log_measurement(self, data: ElectricalMeasurement) -> None:
        self._logger.warning("Temp: %0.3f°C", data.temperature)

    def log(self, data: List[ElectricalMeasurement]) -> None:
        self._log_measurement(data[-1])
