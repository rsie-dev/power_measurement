import logging
from concurrent.futures import Executor
import datetime
from dataclasses import dataclass

from humanize import naturaldelta

from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentRuntime
from experiment.run.base import ExperimentResources
from experiment.run.log import LogDispatcher, Logger
from experiment.run.log import TemperatureEntry
from experiment.log_util import TimeThrottleFilter

from .step import Step
from .measurement_step import MeasurementAbort
from .time_format import format_temp


class TempMonitorStep(Step, Logger[TemperatureEntry], MeasurementAbort):
    TEMP_UPDATE_LOG_NAME = None

    @dataclass
    class RunContext:
        threshold_high: float | None = None
        threshold_low: float | None = None
        start_time: datetime.datetime | None = None
        abort_flag: bool = False

    def __init__(self, log_dispatcher: LogDispatcher[TemperatureEntry], max_temp_delta: float,
                 min_duration: datetime.timedelta | None = None, now=datetime.datetime.now):
        super().__init__("temperature monitor")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._log_dispatcher = log_dispatcher
        self._max_temp_delta = max_temp_delta
        if min_duration is None:
            min_duration = datetime.timedelta(seconds=2)
        self._min_duration = min_duration
        self._now = now
        self._context = TempMonitorStep.RunContext()
        if TempMonitorStep.TEMP_UPDATE_LOG_NAME is None:
            TempMonitorStep.TEMP_UPDATE_LOG_NAME = self.__class__.__name__ + ".UPDATE"
            logger = logging.getLogger(TempMonitorStep.TEMP_UPDATE_LOG_NAME)
            logger.addFilter(TimeThrottleFilter(datetime.timedelta(seconds=30)))

    def abort_measurement(self) -> bool:
        return self._context.abort_flag

    def execute(self, runtime: ExperimentRuntime) -> None:
        pass

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources) -> None:
        pass

    def start(self, runtime: ExperimentRuntime, executor: Executor) -> None:
        self._logger.debug("temperature monitor start")
        self._log_dispatcher.register_logger(self)

    def stop(self, runtime: ExperimentRuntime) -> None:
        self._log_dispatcher.unregister_logger(self)
        self._logger.debug("temperature monitor stop")

    def _log_measurement(self, data: TemperatureEntry) -> None:
        if self._context.abort_flag:
            return

        if self._context.threshold_high is None:
            initial_temperature = data.temperature
            self._context.threshold_high = initial_temperature + self._max_temp_delta
            self._context.threshold_low = initial_temperature - self._max_temp_delta
            self._logger.info("Initial temp: %s -> thresholds: %s -- %s",
                              format_temp(initial_temperature),
                              format_temp(self._context.threshold_low),
                              format_temp(self._context.threshold_high))
            return

        now = self._now()

        if data.temperature < self._context.threshold_low:
            if self._context.start_time is None:
                self._logger.warning("Temp is below lower threshold (%s): %s",
                                     format_temp(self._context.threshold_low),
                                     format_temp(data.temperature))
                self._context.start_time = now
            elif now - self._context.start_time > self._min_duration:
                self._logger.fatal("Temp is below lower threshold %s for more than %s -> abort",
                                   format_temp(self._context.threshold_low),
                                   naturaldelta(self._min_duration))
                self._context.abort_flag = True
            else:
                self._log_update("Temp is still below lower threshold (%s): %s" %
                                 (format_temp(self._context.threshold_low),
                                  format_temp(data.temperature)))
        elif data.temperature > self._context.threshold_high:
            if self._context.start_time is None:
                self._logger.warning("Temp is above upper threshold (%s): %s",
                                     format_temp(self._context.threshold_high),
                                     format_temp(data.temperature))
                self._context.start_time = now
            elif now - self._context.start_time > self._min_duration:
                self._logger.fatal("Temp is above upper threshold %s for more than %s -> abort",
                                   format_temp(self._context.threshold_high),
                                   naturaldelta(self._min_duration))
                self._context.abort_flag = True
            else:
                self._log_update("Temp is still above upper threshold (%s): %s" %
                                 (format_temp(self._context.threshold_high),
                                  format_temp(data.temperature)))
        else:
            if self._context.start_time:
                self._logger.warning("Temp is back in range: %s -- %s: %s",
                                     format_temp(self._context.threshold_low),
                                     format_temp(self._context.threshold_high),
                                     format_temp(data.temperature))
            self._context.start_time = None

    def _log_update(self, state):
        logger = logging.getLogger(TempMonitorStep.TEMP_UPDATE_LOG_NAME)
        logger.warning(state)

    def log(self, data: TemperatureEntry | list[TemperatureEntry]) -> None:
        if not isinstance(data, list):
            data = [data]
        self._log_measurement(data[-1])
