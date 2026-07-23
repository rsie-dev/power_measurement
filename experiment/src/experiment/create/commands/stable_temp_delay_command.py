import logging
import datetime
from threading import Condition
from collections import deque
from dataclasses import dataclass

import humanize

from experiment.common import format_temp
from experiment.run.log import Logger
from experiment.run.log import LogDispatcher, TemperatureEntry

from .delay_command import DelayCommand


class StableTemperatureDelayCommand(DelayCommand, Logger[TemperatureEntry]):
    @dataclass(frozen=True)
    class Config:
        min_delay: datetime.timedelta
        max_delay: datetime.timedelta
        kind: str
        temp_dispatcher: LogDispatcher[TemperatureEntry]
        slope_threshold: float
        wait_timeout: float = 1

    @dataclass(frozen=True)
    class State:
        stable: bool
        temperature: float

    def __init__(self, config: Config):
        super().__init__(config.min_delay, config.kind)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config = config
        self._condition = Condition()
        self._history: deque[TemperatureEntry] = deque()

    def execute(self, nr: int, connection) -> None:
        kind = self._kind[:1].upper() + self._kind[1:]
        self._logger.info("%s delay till stable temperature (min: %s max: %s)", kind,
                          humanize.precisedelta(self._config.min_delay), humanize.precisedelta(self._config.max_delay))
        self._history = deque()
        self._config.temp_dispatcher.register_logger(self)
        try:
            start = datetime.datetime.now(datetime.UTC)
            state = self._wait_for_thermal_equilibrium()
            end = datetime.datetime.now(datetime.UTC)
            duration = end - start
            if state.stable:
                self._logger.info("Stable temperature reached after %s at: %s",
                                  humanize.precisedelta(duration), format_temp(state.temperature))
            else:
                self._logger.warning("Max delay of %s elapsed before stable temperature reached (current: %s)",
                                     humanize.precisedelta(self._config.max_delay),
                                     format_temp(state.temperature))
        finally:
            self._config.temp_dispatcher.unregister_logger(self)

    def _wait_for_thermal_equilibrium(self) -> State:
        start = end = datetime.datetime.now(datetime.UTC)
        while end - start < self._config.max_delay:
            with self._condition:
                self._condition.wait(timeout=self._config.wait_timeout)
                history = self._history.copy()

            if self._equilibrium_reached(history):
                return StableTemperatureDelayCommand.State(
                    stable=True,
                    temperature=history[-1].temperature
                )
            end = datetime.datetime.now(datetime.UTC)

        return StableTemperatureDelayCommand.State(
            stable=False,
            temperature=history[-1].temperature
        )

    def _equilibrium_reached(self, history: deque[TemperatureEntry]) -> bool:
        if len(history) < 2:
            return False

        history_start = history[0].timestamp
        history_end = history[-1].timestamp
        history_time = history_end - history_start
        if history_time < self._delay:
            return False

        readings = [t.temperature for t in history]

        slope = self._slope(readings)
        if abs(slope) > self._config.slope_threshold:
            return False

        return True

    def _slope(self, readings: list[float]) -> float:
        """Least-squares slope (°C/sample)."""
        n = len(readings)

        x_mean = (n - 1) / 2
        y_mean = sum(readings) / n

        num = 0.0
        den = 0.0

        for i, y in enumerate(readings):
            dx = i - x_mean
            num += dx * (y - y_mean)
            den += dx * dx

        return num / den

    def log(self, data: TemperatureEntry | list[TemperatureEntry]) -> None:
        if not isinstance(data, list):
            data = [data]
        with self._condition:
            self._append_data(data)
            self._condition.notify()

    def _append_data(self, data: list[TemperatureEntry]):
        self._history.extend(data)
        history_end = self._history[-1].timestamp
        while len(self._history) > 1:
            next_oldest = self._history[1].timestamp
            if history_end - next_oldest < self._delay:
                break
            self._history.popleft()
