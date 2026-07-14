import logging
import datetime
from threading import Condition
from collections import deque
from dataclasses import dataclass

import humanize

from experiment.run.log import Logger
from experiment.run.log import LogDispatcher, TemperatureEntry

from .delay_command import DelayCommand


def format_temp(temp: float) -> str:
    return f"{temp:2.2f}°C"


class TemperatureThresholdDelayCommand(DelayCommand, Logger[TemperatureEntry]):
    @dataclass(frozen=True)
    class Config:
        min_delay: datetime.timedelta
        max_delay: datetime.timedelta
        kind: str
        temp_dispatcher: LogDispatcher[TemperatureEntry]
        threshold: float
        wait_timeout: float = 5

    def __init__(self, config: Config):
        super().__init__(config.min_delay, config.kind)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config = config
        self._condition = Condition()
        self._history: deque[TemperatureEntry] = deque()

    def execute(self, nr: int, connection) -> None:
        kind = self._kind[:1].upper() + self._kind[1:]
        self._logger.info("%s delay till temperature equilibrium (min: %s max: %s)", kind,
                          humanize.naturaldelta(self._config.min_delay), humanize.naturaldelta(self._config.max_delay))
        self._history = deque()
        self._config.temp_dispatcher.register_logger(self)
        try:
            start = datetime.datetime.now(datetime.UTC)
            new_equilibrium = self._wait_for_thermal_equilibrium()
            end = datetime.datetime.now(datetime.UTC)
            duration = end - start
            if new_equilibrium is not None:
                self._logger.info("Temperature equilibrium reached after %s at: %s",
                                  humanize.naturaldelta(duration), format_temp(new_equilibrium))
            else:
                self._logger.warning("Max delay of %s elapsed before temperature equilibrium reached",
                                     humanize.naturaldelta(self._config.max_delay))
        finally:
            self._config.temp_dispatcher.unregister_logger(self)

    def _wait_for_thermal_equilibrium(self) -> float | None:
        start = end = datetime.datetime.now(datetime.UTC)
        while end - start < self._config.max_delay:
            with self._condition:
                self._condition.wait(timeout=self._config.wait_timeout)
                history = self._history.copy()

            if self._equilibrium_reached(history):
                return history[-1].temperature
            end = datetime.datetime.now(datetime.UTC)
        return None

    def _equilibrium_reached(self, history: deque[TemperatureEntry]) -> bool:
        if len(history) < 2:
            return False
        readings = [t.temperature for t in history]
        temp_delta = max(readings) - min(readings)
        #self._logger.warning(f"sample # {len(history)} min: {min(readings)} max: {max(readings)} delta: {temp_delta}")
        history_start = history[0].timestamp
        history_end = history[-1].timestamp
        history_time = history_end - history_start
        if history_time < self._delay:
            return False
        readings = [t.temperature for t in history]
        temp_delta = max(readings) - min(readings)
        if temp_delta > self._config.threshold:
            return False
        return True

    def log(self, data: TemperatureEntry | list[TemperatureEntry]) -> None:
        if not isinstance(data, list):
            data = [data]
        with self._condition:
            self._append_data(data)
            self._condition.notify()

    def _append_data(self, data: list[TemperatureEntry]):
        self._history.extend(data)
        cutoff = data[-1].timestamp - (self._delay + datetime.timedelta(seconds=1))
        while self._history and self._history[0].timestamp < cutoff:
            self._history.popleft()
