import logging
import threading
from concurrent.futures import Executor, wait, FIRST_EXCEPTION

from app.usb_meter import devices_by_serial_number, USBMeter
from app.usb_meter.device import Device
from .step import Step
from .experiment_environment import ExperimentEnvironment
from .experiment_runtime import ExperimentRuntime
from .experiment_measurement import ExperimentMeasurement
from .csv_electrical_logger import CSVElectricLogger
from .signal_stop_provider import SignalStopProvider


class USBMeterStep(Step):
    def __init__(self, _host: str, serial_number: str):
        super().__init__("USB meter")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._serial_number = serial_number
        self._usb_meter = None
        self._electrical_log = None
        self._stop_provider = None
        self._start_timeout = 3
        self._future = None

    def _find_device(self) -> Device:
        devices = devices_by_serial_number(self._serial_number)
        device = next(devices, None)
        if not device:
            raise RuntimeError("No devices found with: %s" % self._serial_number)
        if next(devices, None):
            raise RuntimeError("Too many devices found with: %s" % self._serial_number)
        return device

    def _electric_collector(self, usb_meter, electrical_log, event):
        self._logger.info("USB meter start")
        event.set()
        try:
            with CSVElectricLogger(electrical_log, latest_only=True) as data_logger:
                usb_meter.run(data_logger)
        finally:
            self._logger.info("USB meter shut down")

    def init(self, environment: ExperimentEnvironment, measurement: ExperimentMeasurement):
        device = self._find_device()
        self._stop_provider = SignalStopProvider()
        environment.add_shutdown_handler(self._stop_provider)
        self._usb_meter = USBMeter(device=device, stop_provider=self._stop_provider, use_crc=True)
        self._usb_meter.setup_device()
        self._electrical_log = environment.get_resources_path() / "electrical.csv"

    def start(self, executor: Executor):
        event = threading.Event()
        future = executor.submit(self._electric_collector, self._usb_meter, self._electrical_log, event)
        event.wait(self._start_timeout)
        self._future = future

    def stop(self, runtime: ExperimentRuntime, measurement: ExperimentMeasurement):
        if self._stop_provider:
            self._stop_provider.shut_down(False)

        wait([self._future], return_when=FIRST_EXCEPTION)
        self._future.result()
