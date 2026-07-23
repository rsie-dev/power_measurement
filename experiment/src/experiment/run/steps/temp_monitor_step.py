import logging
from concurrent.futures import Executor
import datetime
from dataclasses import dataclass

from humanize import naturaldelta

from experiment.common import format_temp
from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentRuntime
from experiment.run.base import ExperimentResources
from experiment.run.log import LogDispatcher, Logger
from experiment.run.log import TemperatureEntry
from experiment.log_util import TimeThrottleFilter

from .step import Step
from .measurement_step import MeasurementAbort


class TempMonitorStep(Step, Logger[TemperatureEntry], MeasurementAbort):
    TEMP_UPDATE_LOG_NAME = None

    @dataclass(frozen=True)
    class Config:
        kind: str
        log_dispatcher: LogDispatcher[TemperatureEntry]
        max_temp_delta: float
        min_duration: datetime.timedelta

    @dataclass
    class RunContext:
        threshold_high: float | None = None
        threshold_low: float | None = None
        start_time: datetime.datetime | None = None
        abort_flag: bool = False

    def __init__(self, config: Config, now=datetime.datetime.now):
        super().__init__("temperature monitor")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config = config
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
        self._logger.debug("%s temperature monitor start", self._config.kind)
        self._config.log_dispatcher.register_logger(self)

    def stop(self, runtime: ExperimentRuntime) -> None:
        self._config.log_dispatcher.unregister_logger(self)
        self._logger.debug("%s temperature monitor stop", self._config.kind)

    def _log_measurement(self, data: TemperatureEntry) -> None:
        if self._context.abort_flag:
            return

        if self._context.threshold_high is None:
            initial_temperature = data.temperature
            self._context.threshold_high = initial_temperature + self._config.max_temp_delta
            self._context.threshold_low = initial_temperature - self._config.max_temp_delta
            self._logger.info("Initial %s temp: %s -> thresholds: %s -- %s", self._config.kind,
                              format_temp(initial_temperature),
                              format_temp(self._context.threshold_low),
                              format_temp(self._context.threshold_high))
            return

        now = self._now()

        kind = self._config.kind[:1].upper() + self._config.kind[1:]
        if data.temperature < self._context.threshold_low:
            if self._context.start_time is None:
                self._logger.warning("%s temp is below lower threshold (%s): %s", kind,
                                     format_temp(self._context.threshold_low),
                                     format_temp(data.temperature))
                self._context.start_time = now
            elif now - self._context.start_time > self._config.min_duration:
                self._logger.fatal("%s temp is below lower threshold %s for more than %s -> abort", kind,
                                   format_temp(self._context.threshold_low),
                                   naturaldelta(self._config.min_duration))
                self._context.abort_flag = True
            else:
                self._log_update("%s temp is still below lower threshold (%s): %s" %
                                 (kind, format_temp(self._context.threshold_low),
                                  format_temp(data.temperature)))
        elif data.temperature > self._context.threshold_high:
            if self._context.start_time is None:
                self._logger.warning("%s temp is above upper threshold (%s): %s", kind,
                                     format_temp(self._context.threshold_high),
                                     format_temp(data.temperature))
                self._context.start_time = now
            elif now - self._context.start_time > self._config.min_duration:
                self._logger.fatal("%s temp is above upper threshold %s for more than %s -> abort", kind,
                                   format_temp(self._context.threshold_high),
                                   naturaldelta(self._config.min_duration))
                self._context.abort_flag = True
            else:
                self._log_update("%s temp is still above upper threshold (%s): %s" %
                                 (kind, format_temp(self._context.threshold_high),
                                  format_temp(data.temperature)))
        else:
            if self._context.start_time:
                self._logger.warning("%s temp is back in range: %s -- %s: %s", kind,
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
