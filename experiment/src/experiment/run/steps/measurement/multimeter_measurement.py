import logging
from threading import Event, RLock
from concurrent.futures import Executor, wait, FIRST_EXCEPTION
from dataclasses import dataclass

from usb_multimeter import USBMeter, ElectricalMeasurement

from experiment.run.log import LogDispatcher
from experiment.run.base import ExperimentEnvironment
from experiment.common import DeviceManager
from experiment.common import format_temp
from experiment.common import MeasurementAbort

from .measurement import Measurement
from .signal_stop_provider import SignalStopProvider


class MultimeterMeasurement(Measurement, MeasurementAbort):
    @dataclass(frozen=True)
    class Config:
        device_manager: DeviceManager
        log_dispatcher: LogDispatcher[ElectricalMeasurement]

    @dataclass
    class Context:
        failure: Exception | None = None
        failure_lock = RLock()
        temp_offset: float| int = 0

    def __init__(self, config: Config):
        super().__init__("multimeter")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config = config
        self._context = MultimeterMeasurement.Context()
        self._usb_meter = None
        self._stop_provider = None
        self._start_timeout = 3
        self._future = None

    def set_temp_offset(self, temp_offset: float | int) -> None:
        self._context.temp_offset = temp_offset

    def get_abort_reason(self) -> Exception | None:
        with self._context.failure_lock:
            return self._context.failure

    def _set_failure(self, failure: Exception) -> None:
        with self._context.failure_lock:
            self._context.failure = failure

    def start(self, environment: ExperimentEnvironment, executor: Executor):
        self._prepare()
        event = Event()
        future = executor.submit(self._electric_collector, self._usb_meter, event)
        event.wait(self._start_timeout)
        self._future = future

    def _prepare(self):
        if self._context.temp_offset:
            self._logger.info("Using temperature offset of: %s", format_temp(self._context.temp_offset))

        self._stop_provider = SignalStopProvider()
        device = self._config.device_manager.get_device()
        config = USBMeter.Config(
            device=device,
            stop_provider=self._stop_provider,
            use_crc=True,
            temp_offset=self._context.temp_offset,
        )
        self._usb_meter = USBMeter(config)
        self._usb_meter.setup_device()

    def _electric_collector(self, usb_meter: USBMeter, event: Event) -> None:
        self._logger.debug("multimeter thread running")
        event.set()
        try:
            usb_meter.run(self._config.log_dispatcher)
        except Exception as e:   # pylint: disable=broad-exception-caught
            self._logger.fatal("%s -> abort", e)
            self._set_failure(e)
        finally:
            self._logger.debug("multimeter thread stopped")

    def stop(self, environment: ExperimentEnvironment):
        if self._stop_provider:
            self._stop_provider.shut_down(False)

        wait([self._future], return_when=FIRST_EXCEPTION)
        self._future.result()
