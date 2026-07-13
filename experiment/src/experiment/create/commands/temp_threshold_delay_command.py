import logging
import datetime
from threading import Condition
from collections import deque

import humanize

from experiment.run.log import Logger
from experiment.run.log import LogDispatcher, TemperatureEntry

from .delay_command import DelayCommand


def format_temp(temp: float) -> str:
    return f"{temp:2.2f}°C"


class TemperatureThresholdDelayCommand(DelayCommand, Logger[TemperatureEntry]):
    def __init__(self, delay: datetime.timedelta, kind: str, temp_dispatcher: LogDispatcher[TemperatureEntry],
                 min_delay: datetime.timedelta, threshold: float):
        super().__init__(min_delay, kind)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._temp_dispatcher = temp_dispatcher
        self._max_delay = delay
        self._threshold = threshold
        self._wait_timeout = 5
        self._condition = Condition()
        self._history: deque[TemperatureEntry] = deque()

    def execute(self, nr: int, connection) -> None:
        kind = self._kind[:1].upper() + self._kind[1:]
        self._logger.info("%s delay till temperature equilibrium (min: %s max: %s)", kind,
                          humanize.naturaldelta(self._delay), humanize.naturaldelta(self._max_delay))
        self._history = deque()
        self._temp_dispatcher.register_logger(self)
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
                                     humanize.naturaldelta(self._max_delay))
        finally:
            self._temp_dispatcher.unregister_logger(self)

    def _wait_for_thermal_equilibrium(self) -> float | None:
        start = end = datetime.datetime.now(datetime.UTC)
        while end - start < self._max_delay:
            with self._condition:
                self._condition.wait(timeout=self._wait_timeout)
                history = self._history.copy()

            if self._equilibrium_reached(history):
                return history[-1].temperature
            end = datetime.datetime.now(datetime.UTC)
        return None

    def _equilibrium_reached(self, history: deque[TemperatureEntry]):
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
        if temp_delta > self._threshold:
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
