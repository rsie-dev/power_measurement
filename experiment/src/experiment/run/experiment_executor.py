import logging
from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_EXCEPTION
from threading import Event
from contextlib import ExitStack

from experiment.api import Experiment
from experiment.system_meter import MetricsServer, SystemMeasurement
from experiment.ssh import SSHManager, SSHConnectionManager, ConnectionFactory
from .steps import Step, InitStep
from .log import LogDispatcher
from .environment import Environment, InitialEnvironment
from .runtime import Runtime
from .experiment_runner import ExperimentRunner


class ExperimentExecutor(Experiment):
    def __init__(self, connection_factory: ConnectionFactory, init_steps: List[InitStep], steps: List[Step],
                 metrics_dispatcher: LogDispatcher[SystemMeasurement]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._connection_factory = connection_factory
        self._init_steps: List[InitStep] = init_steps
        self._steps: List[Step] = steps
        self._metrics_dispatcher = metrics_dispatcher
        self._server_start_timeout: float = 3

    def run(self, resources: Path, metrics_server_address: tuple[str, int]):
        with SSHConnectionManager(self._connection_factory) as ssh_manager:
            runtime = Runtime(ssh_manager)
            self._initialize(runtime, self._init_steps)

            with ThreadPoolExecutor() as executor:
                futures = []
                try:
                    with ExitStack() as stack:
                        if self._metrics_dispatcher:
                            future = self._init_metrics_server(executor, stack, metrics_server_address)
                            futures.append(future)

                        environment = Environment(ssh_manager, metrics_server_address)
                        runner = ExperimentRunner(executor, resources, self._steps)
                        runner.execute_runs(runtime, environment)
                finally:
                    if futures:
                        self._logger.info("Wait for threads")
                        done, _ = wait(futures, return_when=FIRST_EXCEPTION)
                        for future in done:
                            future.result()

    def _init_metrics_server(self, executor: ThreadPoolExecutor, stack: ExitStack, server_address: tuple[str, int]):
        metrics_server = stack.enter_context(MetricsServer(server_address))
        event = Event()
        future = executor.submit(self._system_collector, metrics_server, self._metrics_dispatcher, event)
        event.wait(self._server_start_timeout)
        return future

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
