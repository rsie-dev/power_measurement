import logging
from typing import List
from pathlib import Path
from concurrent.futures import Executor, ThreadPoolExecutor, wait, FIRST_EXCEPTION
import threading
import contextlib

from fabric import Connection

from app.common import SignalHandler
from app.common import ShutdownHandler
from app.system_meter import MetricsServer
from .steps.experiment_environment import ExperimentEnvironment
from .steps.experiment_runtime import ExperimentRuntime
from .steps import Step
from .ssh_manager import SSHManager
from .measurement_dispatcher import MeasurementDispatcher
from .steps.csv_system_logger import CSVSystemLogger


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

    def _run_experiment(self, environment: ExperimentEnvironment, runtime: ExperimentRuntime,
                        steps, signal_handler, executor: Executor):
        self._logger.info("Initialize all steps")
        for step in steps:
            self._logger.debug("init step: %s", step.name)
            step.init(environment)

        try:
            self._logger.info("Starting all steps")
            for step in steps:
                self._logger.debug("start step: %s", step.name)
                step.start(executor)

            try:
                with signal_handler.capture_signals():
                    for step in steps:
                        self._logger.debug("execute step: %s", step.name)
                        step.execute(runtime)
            except KeyboardInterrupt:
                pass

        finally:
            self._logger.info("Stopping all steps")
            for step in list(reversed(steps)):
                self._logger.debug("stop step: %s", step.name)
                step.stop(runtime)
            self._logger.info("Stopped all steps")

    def _execute_runs(self, ssh_manager: SSHManager, runs_resources: Path, signal_handler: SignalHandler,
                      measurement_dispatcher: MeasurementDispatcher, executor: Executor):
        steps = self._steps[:]
        for run in range(self._runs):
            self._logger.info("Start run %d/%d", run + 1, self._runs)
            run_resource = runs_resources / ("run_%03d" % (run + 1))
            run_resource.mkdir(parents=True, exist_ok=True)

            class Environment(ExperimentEnvironment):
                def __init__(self, ssh_manager: SSHManager, signal_handler: SignalHandler,
                             measurement_dispatcher: MeasurementDispatcher, resource_path: Path,
                             metrics_server_host: str, metrics_server_port: int):
                    self._ssh_manager = ssh_manager
                    self._signal_handler = signal_handler
                    self._measurement_dispatcher = measurement_dispatcher
                    self._resource_path = resource_path
                    self._metrics_server_host: str = metrics_server_host
                    self._metrics_server_port: int = metrics_server_port

                def get_metrics_server(self) -> str:
                    return "%s:%s" % (self._metrics_server_host, self._metrics_server_port)

                def get_resources_path(self) -> Path:
                    return self._resource_path

                def add_shutdown_handler(self, handler: ShutdownHandler) -> None:
                    self._signal_handler.add_shutdown_handler(handler)

                def register_for_system_meter(self, host: str) -> None:
                    metric_file_path = self.get_resources_path() / "system.csv"
                    self._measurement_dispatcher.add_logger(host, CSVSystemLogger(metric_file_path))

                def register_ssh_connection(self, user: str, host: str) -> None:
                    self._ssh_manager.register_ssh_connection(user, host)

            class Runtime(ExperimentRuntime):
                def __init__(self, ssh_manager: SSHManager, measurement_dispatcher: MeasurementDispatcher):
                    self._ssh_manager = ssh_manager
                    self._measurement_dispatcher = measurement_dispatcher

                def get_ssh_connection(self, user: str, host: str) -> Connection:
                    return self._ssh_manager.get_ssh_connection(user, host)

                def unregister_for_system_meter(self, host: str) -> None:
                    logger = measurement_dispatcher.remove_logger(host)
                    if logger:
                        logger.close()

            environment = Environment(ssh_manager, signal_handler, measurement_dispatcher, run_resource,
                                      self._metrics_server_host, self._metrics_server_port)
            runtime = Runtime(ssh_manager, measurement_dispatcher)
            self._run_experiment(environment, runtime, steps, signal_handler, executor)

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
                        self._execute_runs(ssh_manager, runs_resources, signal_handler, md, executor)
            finally:
                if future:
                    metrics_server.shut_down(False)
                    self._logger.info("Wait for system_meter")
                    wait([future], return_when=FIRST_EXCEPTION)
                    if future.done():
                        future.result()
