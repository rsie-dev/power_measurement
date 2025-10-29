import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait

from system_meter import MetricsServer
from usb_meter import USBMeter
from usb_meter.device import Device

from experiment_api import E

from .csv_system_logger import CSVSystemLogger
from .csv_electrical_logger import CSVElectricLogger
from .signal_handler import SignalHandler
from .signal_stop_provider import SignalStopProvider
from .experiment_loader import ExperimentLoader


class Runner:
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def _system_collector(self, metrics_server, args):
        self._logger.debug("REST system_meter start")
        try:
            with CSVSystemLogger(Path(args.system)) as dl:
                metrics_server.run(args, dl)
        finally:
            self._logger.debug("REST system_meter shut down")

    def _electric_collector(self, usb_meter, args):
        self._logger.info("USB meter start")
        try:
            with CSVElectricLogger(Path(args.electrical), args.latest_only) as data_logger:
                usb_meter.run(data_logger)
        finally:
            self._logger.info("USB meter shut down")

    def _run_experiment(self, device: Device, args):
        signal_handler = SignalHandler()
        metrics_server = MetricsServer()
        signal_handler.add_shutdown_handler(metrics_server)

        stop_provider = SignalStopProvider()
        signal_handler.add_shutdown_handler(stop_provider)
        usb_meter = USBMeter(device=device, stop_provider=stop_provider, crc=True)
        usb_meter.setup_device()
        usb_meter.initialize_communication()
        try:
            with signal_handler.capture_signals():
                with ThreadPoolExecutor() as executor:
                    sc = executor.submit(self._system_collector, metrics_server, args)
                    ec = executor.submit(self._electric_collector, usb_meter, args)
                    wait([sc, ec])
        except KeyboardInterrupt:
            pass

    def run_experiment(self, _device: Device, _args):
        experiment_loader = ExperimentLoader()
        experiment_loader.load_steps_from_path(Path("e_steps.py"))
        E.run()
