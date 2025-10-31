import logging
from getpass import getpass
from concurrent.futures import Executor

from fabric import Connection

from app.usb_meter import devices_by_serial_number
from app.usb_meter.device import Device
from app.usb_meter import USBMeter
from app.run.signal_stop_provider import SignalStopProvider
from app.run.csv_electrical_logger import CSVElectricLogger
from .experiment_environment import ExperimentEnvironment


class Step:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self):
        return self._name

    def init(self, environment: ExperimentEnvironment):
        pass

    def start(self, executor: Executor):
        pass

    def stop(self):
        pass

    def execute(self):
        pass


class USBMeterStep(Step):
    def __init__(self, host: str, serial_number: str):
        super().__init__("host")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host
        self._serial_number = serial_number
        self._usb_meter = None
        self._electrical_log = None
        self._stop_provider = None

    def _find_device(self) -> Device:
        devices = devices_by_serial_number(self._serial_number)
        device = next(devices, None)
        if not device:
            raise RuntimeError("No devices found with: %s" % self._serial_number)
        if next(devices, None):
            raise RuntimeError("Too many devices found with: %s" % self._serial_number)
        return device

    def _electric_collector(self, usb_meter, electrical_log):
        self._logger.info("USB meter start")
        try:
            with CSVElectricLogger(electrical_log, latest_only=True) as data_logger:
                usb_meter.run(data_logger)
        finally:
            self._logger.info("USB meter shut down")

    def init(self, environment: ExperimentEnvironment):
        device = self._find_device()
        self._stop_provider = SignalStopProvider()
        environment.add_shutdown_handler(self._stop_provider)
        self._usb_meter = USBMeter(device=device, stop_provider=self._stop_provider, use_crc=True)
        self._usb_meter.setup_device()
        self._electrical_log = environment.get_resources_path() / "electrical.csv"

    def start(self, executor: Executor):
        return executor.submit(self._electric_collector, self._usb_meter, self._electrical_log)

    def stop(self):
        if not self._stop_provider:
            return
        self._stop_provider.shut_down(False)


class HostCommandStep(Step):
    def __init__(self,  host_name: str, ssh_user: str, commands):
        super().__init__("host command")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host_name = host_name
        self._ssh_user = ssh_user
        self._commands = commands

    def execute(self):
        self._logger.info("on host: %s execute: %s", self._host_name, ",".join(self._commands))
        password = getpass(f'SSH password for {self._ssh_user}@{self._host_name}: ')
        connect_kwargs = {
            "password": password,
        }
        with Connection(self._host_name, user=self._ssh_user, connect_kwargs=connect_kwargs) as con:
            for command in self._commands:
                con.run(command, hide=True)
        self._logger.info("commands executed")
