import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait

from app.system_meter import MetricsServer
from app.usb_meter import USBMeter
from app.usb_meter.device import Device

from .csv_system_logger import CSVSystemLogger
from .csv_electrical_logger import CSVElectricLogger
from .signal_handler import SignalHandler
from .signal_stop_provider import SignalStopProvider
from .experiment_loader import ExperimentLoader


class Runner:
    def __init__(self, resources: Path):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._resources = resources

    def _system_collector(self, metrics_server, host: str, port: int, args):
        self._logger.debug("REST system_meter start")
        try:
            with CSVSystemLogger(Path(args.system)) as dl:
                metrics_server.run(host, port, dl)
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
        usb_meter = USBMeter(device=device, stop_provider=stop_provider, use_crc=True)
        usb_meter.setup_device()
        try:
            with signal_handler.capture_signals():
                with ThreadPoolExecutor() as executor:
                    sc = executor.submit(self._system_collector, metrics_server, args.host, args.port, args)
                    ec = executor.submit(self._electric_collector, usb_meter, args)
                    wait([sc, ec])
        except KeyboardInterrupt:
            pass

    def run_experiment(self, args):
        experiment_loader = ExperimentLoader()
        experiment_module = Path(args.experiment[0])
        experiment = experiment_loader.load_steps_from_path(experiment_module)
        resources = self._resources / experiment_module.stem
        self._logger.info("experiment resources: %s", resources)
        resources.mkdir(parents=True, exist_ok=True)
        signal_handler = SignalHandler()
        try:
            with signal_handler.capture_signals():
                experiment.run(resources, signal_handler)
        except KeyboardInterrupt:
            pass
