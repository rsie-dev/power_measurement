import logging
from threading import Event
from concurrent.futures import Executor, wait, FIRST_EXCEPTION

from usb_multimeter import USBMeter, ElectricalMeasurement
from usb_multimeter.device import Device

from app.experiment.log import LogDispatcher
from app.experiment.base import ExperimentEnvironment
from .measurement import Measurement
from .signal_stop_provider import SignalStopProvider


class MultimeterMeasurement(Measurement):
    def __init__(self, device: Device, log_dispatcher: LogDispatcher[ElectricalMeasurement]):
        super().__init__("multimeter")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._device = device
        self._usb_meter = None
        self._stop_provider = None
        self._start_timeout = 3
        self._future = None
        self._log_dispatcher = log_dispatcher

    def start(self, environment: ExperimentEnvironment, executor: Executor):
        self._prepare(environment)
        event = Event()
        future = executor.submit(self._electric_collector, self._usb_meter, event)
        event.wait(self._start_timeout)
        self._future = future

    def _prepare(self, environment: ExperimentEnvironment):
        self._stop_provider = SignalStopProvider()
        environment.add_shutdown_handler(self._stop_provider)
        self._usb_meter = USBMeter(device=self._device, stop_provider=self._stop_provider, use_crc=True)
        self._usb_meter.setup_device()

    def _electric_collector(self, usb_meter: USBMeter, event: Event) -> None:
        self._logger.debug("multimeter thread running")
        event.set()
        try:
            usb_meter.run(self._log_dispatcher)
        finally:
            self._logger.debug("multimeter thread stopped")

    def stop(self, environment: ExperimentEnvironment):
        if self._stop_provider:
            environment.remove_shutdown_handler(self._stop_provider)
            self._stop_provider.shut_down(False)

        wait([self._future], return_when=FIRST_EXCEPTION)
        self._future.result()
