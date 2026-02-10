import logging
from typing import List
from pathlib import Path
from concurrent.futures import Executor, ThreadPoolExecutor, wait, FIRST_EXCEPTION
import threading
import contextlib


from app.common import SignalHandler
from app.system_meter import MetricsServer
from .steps.experiment_environment import ExperimentEnvironment
from .steps.experiment_runtime import ExperimentRuntime
from .steps.experiment_measurement import ExperimentMeasurement
from .steps import Step
from .ssh_manager import SSHManager
from .measurement_dispatcher import MeasurementDispatcher
from .environment import Environment
from .runtime import Runtime
from .measurement import Measurement


class Experiment:
    def __init__(self, steps: List[Step], runs: int, with_metrics_server: bool):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._steps: List[Step] = steps[:]
        self._runs: int = runs
        self._with_metrics_server: bool = with_metrics_server
        # ToDo: find out local IP address
        self._metrics_server_host: str = "192.168.1.190"
        self._metrics_server_port: int = 10000
        self._metrics_server_start_timeout: float = 3

    def _run_experiment(self, environment: ExperimentEnvironment, runtime: ExperimentRuntime,
                        measurement: ExperimentMeasurement, signal_handler, executor: Executor):
        self._logger.info("Initialize all steps")
        for step in self._steps:
            self._logger.debug("init step: %s", step.name)
            step.init(environment, measurement)

        try:
            self._logger.info("Starting all steps")
            for step in self._steps:
                self._logger.debug("start step: %s", step.name)
                step.start(executor)

            try:
                with signal_handler.capture_signals():
                    for step in self._steps:
                        self._logger.debug("execute step: %s", step.name)
                        step.execute(runtime)
            except KeyboardInterrupt:
                pass

        finally:
            self._logger.info("Stopping all steps")
            for step in list(reversed(self._steps)):
                self._logger.debug("stop step: %s", step.name)
                step.stop(runtime, measurement)
            self._logger.info("Stopped all steps")

    def _execute_runs(self, runs_resources: Path, signal_handler: SignalHandler,
                      measurement_dispatcher: MeasurementDispatcher, executor: Executor, runtime: Runtime):
        for run in range(self._runs):
            self._logger.info("Start run %d/%d", run + 1, self._runs)
            run_resource = runs_resources / ("run_%03d" % (run + 1))
            run_resource.mkdir(parents=True, exist_ok=True)
            measurement = Measurement(measurement_dispatcher, run_resource)
            ssh_manager = runtime.ssh_manager
            metrics_server = "%s:%s" % (self._metrics_server_host, self._metrics_server_port)
            environment = Environment(ssh_manager, signal_handler, run_resource, metrics_server)
            self._run_experiment(environment, runtime, measurement, signal_handler, executor)

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
                        self._execute_runs(runs_resources, signal_handler, md, executor, runtime)
            finally:
                if future:
                    metrics_server.shut_down(False)
                    self._logger.info("Wait for system_meter")
                    wait([future], return_when=FIRST_EXCEPTION)
                    if future.done():
                        future.result()
