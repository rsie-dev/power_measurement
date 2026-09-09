import logging
from threading import Event, RLock
from concurrent.futures import Executor, wait, FIRST_EXCEPTION
from dataclasses import dataclass, field
import time
import datetime

from experiment.run.log import LogDispatcher
from experiment.run.log import TemperatureEntry
from experiment.run.base import ExperimentResources
from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentRuntime
from experiment.sensor import SensorDevice
from experiment.common import format_temp
from experiment.common import MeasurementAbort

from .step import Step


class TempSensorStep(Step, MeasurementAbort):
    @dataclass(frozen=True)
    class Config:
        sensor_device: SensorDevice
        log_dispatcher: LogDispatcher[TemperatureEntry]
        temp_offset: float
        bus_name: str = field(init=False)

        def __post_init__(self) -> None:
            object.__setattr__(
                self,
                "bus_name",
                self.sensor_device.device_info.bus,
            )

    @dataclass
    class Context:
        stop_event = Event()
        failure: Exception | None = None
        failure_lock = RLock()

    def __init__(self, config: Config):
        super().__init__("temperature sensor")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config = config
        self._context = TempSensorStep.Context()
        self._start_timeout = 3
        self._future = None

    def get_abort_reason(self) -> Exception | None:
        with self._context.failure_lock:
            return self._context.failure

    def _set_failure(self, failure: Exception) -> None:
        with self._context.failure_lock:
            self._context.failure = failure

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources) -> None:
        pass

    def start(self, runtime: ExperimentRuntime, executor: Executor) -> None:
        self._prepare()
        start_event = Event()
        future = executor.submit(self._temperature_collector, start_event)
        start_event.wait(self._start_timeout)
        self._future = future

    def execute(self, runtime: ExperimentRuntime) -> None:
        pass

    def _prepare(self):
        if self._config.temp_offset:
            self._logger.info("Using temperature offset on %s of: %s",
                              self._config.bus_name,
                              format_temp(self._config.temp_offset))

    def _temperature_collector(self, start_event: Event) -> None:
        self._logger.debug("temperature sensor thread on %s running", self._config.bus_name)
        start_event.set()
        try:
            with self._config.sensor_device as device:
                self._temperature_loop(device)
        except Exception as e:   # pylint: disable=broad-exception-caught
            self._logger.fatal("%s on %s -> abort", e, self._config.bus_name)
            self._set_failure(e)
        finally:
            self._logger.debug("temperature sensor thread on %s stopped", self._config.bus_name)

    def _temperature_loop(self, sensor_device: SensorDevice) -> None:
        interval = 1 / 2  # 5 calls per second
        next_run = time.monotonic()

        while not self._context.stop_event.is_set():
            temperature = sensor_device.get_temperature()
            temperature += self._config.temp_offset
            self._logger.warning("read temp: %.3f", temperature)
            timestamp = datetime.datetime.now(datetime.timezone.utc)
            te = TemperatureEntry(
                timestamp=timestamp,
                temperature=temperature,
            )
            self._config.log_dispatcher.log(te)

            next_run += interval
            remaining = max(0, next_run - time.monotonic())

            if self._context.stop_event.wait(remaining):
                break

    def stop(self, runtime: ExperimentRuntime) -> None:
        self._context.stop_event.set()
        wait([self._future], return_when=FIRST_EXCEPTION)
        self._future.result()
