import logging
from datetime import timedelta
import time
from statistics import mean

import humanize

from experiment.common import TemperatureProvider, format_temp
from experiment.run.base import ExperimentRuntime
from experiment.run.log import Logger
from experiment.run.log import LogDispatcher, TemperatureEntry

from .step import Step


class SBCTemperatureBaselineStep(Step, Logger[TemperatureEntry], TemperatureProvider):
    MIN_SAMPLES = 20

    def __init__(self, sbc_temp_dispatcher: LogDispatcher[TemperatureEntry], sample_time: timedelta):
        super().__init__("SBC temperature baseline")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._sbc_temp_dispatcher = sbc_temp_dispatcher
        self._sample_time = sample_time
        self._samples: list[TemperatureEntry] = []
        self._baseline_temperature = None

    def execute(self, runtime: ExperimentRuntime) -> None:
        self._logger.info("Establishing SBC baseline temperature")
        self._sbc_temp_dispatcher.register_logger(self)
        try:
            self._wait_for_samples(self._sample_time)
            self._baseline_temperature = self._calculate_baseline(self._samples)
            self._logger.info("SBC baseline temperature established at: %s",
                              format_temp(self._baseline_temperature))
        finally:
            self._sbc_temp_dispatcher.unregister_logger(self)

    def _wait_for_samples(self, timeout: timedelta):
        self._logger.info("Collecting SBC temperature samples for %s", humanize.naturaldelta(timeout))
        deadline = time.monotonic() + timeout.total_seconds()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(remaining)

    def log(self, data: TemperatureEntry | list[TemperatureEntry]) -> None:
        if not isinstance(data, list):
            data = [data]
        self._samples.extend(data)

    def _calculate_baseline(self, samples):
        self._logger.debug("collected %d temperature samples", len(samples))
        if len(samples) < self.MIN_SAMPLES:
            raise RuntimeError(f"Too few samples {len(samples)} (min {self.MIN_SAMPLES}) collected")
        readings = [t.temperature for t in samples]
        baseline_temp = mean(readings)
        return baseline_temp

    def get_temp(self) -> float:
        if self._baseline_temperature is None:
            raise RuntimeError("baseline temperature not yet established")
        return self._baseline_temperature
