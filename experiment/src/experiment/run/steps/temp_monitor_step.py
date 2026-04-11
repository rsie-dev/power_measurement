import logging
from concurrent.futures import Executor
from typing import List
import datetime

from usb_multimeter import ElectricalMeasurement

from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentRuntime
from experiment.run.base import ExperimentResources
from experiment.run.log import LogDispatcher, Logger

from .step import Step
from .measurement_step import MeasurementAbort


class TempMonitorStep(Step, Logger, MeasurementAbort):
    def __init__(self, log_dispatcher: LogDispatcher[ElectricalMeasurement], max_temp_delta: float,
                 min_duration: datetime.timedelta | None = None):
        super().__init__("temperature monitor")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._log_dispatcher = log_dispatcher
        self._max_temp_delta = max_temp_delta
        if min_duration is None:
            min_duration = datetime.timedelta(seconds=2)
        self._min_duration = min_duration
        self._threshold = None
        self._start_time = None
        self._abort_flag = False

    def abort_measurement(self) -> bool:
        return self._abort_flag

    def execute(self, runtime: ExperimentRuntime) -> None:
        pass

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources) -> None:
        pass

    def start(self, executor: Executor) -> None:
        self._logger.debug("temperature monitor start")
        self._log_dispatcher.register_logger(self)

    def stop(self, runtime: ExperimentRuntime) -> None:
        self._log_dispatcher.unregister_logger(self)
        self._logger.debug("temperature monitor stop")

    def _log_measurement(self, data: ElectricalMeasurement) -> None:
        if self._threshold is None:
            initial_temperature = data.temperature
            self._threshold = initial_temperature + self._max_temp_delta
            self._logger.info("initial temp: %0.2f°C -> threshold: %0.2f°C", initial_temperature, self._threshold)
            return

        now = datetime.datetime.now()

        if data.temperature > self._threshold:
            if self._start_time is None:
                self._logger.warning("temp is above threshold (%0.2f°C): %0.3f",
                                     self._threshold, data.temperature)
                self._start_time = now
            elif now - self._start_time > self._min_duration:
                self._logger.fatal("temp is above threshold %0.2f°C for more than %s s",
                                   self._threshold, self._min_duration)
                self._abort_flag = True
        else:
            self._start_time = None

    def log(self, data: List[ElectricalMeasurement]) -> None:
        self._log_measurement(data[-1])
