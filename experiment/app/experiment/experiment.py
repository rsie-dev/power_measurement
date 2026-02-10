import logging
from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_EXCEPTION
import threading
import contextlib


from app.common import SignalHandler
from app.system_meter import MetricsServer
from .steps import Step
from .ssh_manager import SSHManager
from .measurement_dispatcher import MeasurementDispatcher
from .environment import Environment
from .runtime import Runtime
from .experiment_runner import ExperimentRunner


class Experiment:
    def __init__(self, steps: List[Step], runs: int, with_metrics_server: bool):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._steps: List[Step] = steps
        self._runs: int = runs
        self._with_metrics_server: bool = with_metrics_server
        # ToDo: find out local IP address
        self._metrics_server_host: str = "192.168.1.190"
        self._metrics_server_port: int = 10000
        self._metrics_server_start_timeout: float = 3

    def _system_collector(self, metrics_server, measurement_dispatcher: MeasurementDispatcher, event):
        def on_startup():
            self._logger.debug("REST system_meter running")
            event.set()

        self._logger.debug("REST system_meter start")
        try:
            metrics_server.run(self._metrics_server_host, self._metrics_server_port, measurement_dispatcher, on_startup)
        finally:
            self._logger.debug("REST system_meter shut down")

    def run(self, resources: Path):
        signal_handler = SignalHandler()
        runs_resources = resources / "runs"
        runs_resources.mkdir(parents=True, exist_ok=True)

        with ThreadPoolExecutor() as executor:
            future = None
            if self._with_metrics_server:
                metrics_server = MetricsServer()
                signal_handler.add_shutdown_handler(metrics_server)
                measurement_dispatcher = MeasurementDispatcher()
            else:
                metrics_server = None
                measurement_dispatcher = contextlib.nullcontext()
            try:
                with measurement_dispatcher as md:
                    if md:
                        event = threading.Event()
                        future = executor.submit(self._system_collector, metrics_server, md, event)
                        event.wait(self._metrics_server_start_timeout)

                    with SSHManager() as ssh_manager:
                        runtime = Runtime(ssh_manager)
                        metrics_server_address = "%s:%s" % (self._metrics_server_host, self._metrics_server_port)
                        environment = Environment(ssh_manager, signal_handler, metrics_server_address)
                        runner = ExperimentRunner(runs_resources, signal_handler, self._steps, self._runs)
                        runner.execute_runs(md, executor, runtime, environment)
            finally:
                if future:
                    metrics_server.shut_down(False)
                    self._logger.info("Wait for system_meter")
                    wait([future], return_when=FIRST_EXCEPTION)
                    if future.done():
                        future.result()
