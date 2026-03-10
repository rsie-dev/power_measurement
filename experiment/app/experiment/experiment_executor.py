import logging
from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_EXCEPTION
from threading import Event

from app.api import Experiment
from app.common import SignalHandler
from app.system_meter import MetricsServer, SystemMeasurement
from .steps import Step, InitStep
from .ssh_manager import SSHManager
from .log import LogDispatcher
from .environment import Environment, InitialEnvironment
from .runtime import Runtime
from .experiment_runner import ExperimentRunner


class ExperimentExecutor(Experiment):
    def __init__(self, init_steps: List[InitStep], steps: List[Step],
                 metrics_dispatcher: LogDispatcher[SystemMeasurement]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._init_steps: List[InitStep] = init_steps
        self._steps: List[Step] = steps
        self._metrics_dispatcher = metrics_dispatcher
        self._metrics_server_start_timeout: float = 3

    def run(self, resources: Path, metrics_server_address: tuple[str, int]):
        with SSHManager() as ssh_manager:
            runtime = Runtime(ssh_manager)
            self._initialize(runtime, self._init_steps)

            signal_handler = SignalHandler()

            with ThreadPoolExecutor() as executor:
                future = None
                if self._metrics_dispatcher:
                    metrics_server = MetricsServer(metrics_server_address)
                    signal_handler.add_shutdown_handler(metrics_server)
                else:
                    metrics_server = None
                try:
                    if self._metrics_dispatcher:
                        event = Event()
                        future = executor.submit(self._system_collector, metrics_server,
                                                 self._metrics_dispatcher, event)
                        event.wait(self._metrics_server_start_timeout)

                    environment = Environment(ssh_manager, signal_handler, metrics_server_address)
                    runner = ExperimentRunner(executor, resources, signal_handler, self._steps)
                    runner.execute_runs(runtime, environment)
                finally:
                    if future:
                        metrics_server.shut_down(False)
                        self._logger.info("Wait for system_meter")
                        wait([future], return_when=FIRST_EXCEPTION)
                        if future.done():
                            future.result()

    def _initialize(self, runtime: Runtime, init_steps: List[InitStep]) -> None:
        if not init_steps:
            return

        initial_environment = InitialEnvironment(runtime.ssh_manager)
        self._logger.info("Initialize %d step(s)", len(init_steps))
        for step in init_steps:
            self._logger.info("Init step: %s", step.name)
            step.init(initial_environment)
            step.execute(runtime)

    def _system_collector(self, metrics_server: MetricsServer, measurement_dispatcher: LogDispatcher[SystemMeasurement],
                          event: Event) -> None:
        def on_startup():
            self._logger.debug("REST system_meter running")
            event.set()

        self._logger.debug("REST system_meter start")
        try:
            metrics_server.run(measurement_dispatcher, on_startup)
        finally:
            self._logger.debug("REST system_meter shut down")
