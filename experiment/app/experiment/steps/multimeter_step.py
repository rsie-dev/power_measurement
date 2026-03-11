import logging
from threading import Event
from concurrent.futures import Executor, wait, FIRST_EXCEPTION


from app.usb_meter import USBMeter
from app.usb_meter.device import Device
from app.usb_meter.measurement import ElectricalMeasurement
from app.experiment.log import LogDispatcher
from .step import Step
from .experiment_environment import ExperimentEnvironment
from .experiment_runtime import ExperimentRuntime
from .experiment_measurement import ExperimentMeasurement
from .experiment_resources import ExperimentResources
from .signal_stop_provider import SignalStopProvider


class MultimeterStep(Step):
    def __init__(self, device: Device, log_dispatcher: LogDispatcher[ElectricalMeasurement]):
        super().__init__("multimeter")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._device = device
        self._usb_meter = None
        self._stop_provider = None
        self._start_timeout = 3
        self._future = None
        self._log_dispatcher = log_dispatcher

    def _electric_collector(self, usb_meter: USBMeter, event: Event) -> None:
        self._logger.info("multimeter start")
        event.set()
        try:
            usb_meter.run(self._log_dispatcher)
        finally:
            self._logger.info("multimeter shut down")

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources):
        self._stop_provider = SignalStopProvider()
        environment.add_shutdown_handler(self._stop_provider)
        self._usb_meter = USBMeter(device=self._device, stop_provider=self._stop_provider, use_crc=True)
        self._usb_meter.setup_device()

    def start(self, executor: Executor, measurement: ExperimentMeasurement):
        event = Event()
        future = executor.submit(self._electric_collector, self._usb_meter, event)
        event.wait(self._start_timeout)
        self._future = future

    def stop(self, runtime: ExperimentRuntime, measurement: ExperimentMeasurement):
        if self._stop_provider:
            self._stop_provider.shut_down(False)

        wait([self._future], return_when=FIRST_EXCEPTION)
        self._future.result()
