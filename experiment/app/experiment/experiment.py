import logging
from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_EXCEPTION

from fabric import Connection

from app.common import SignalHandler
from app.common import ShutdownHandler
from .steps.experiment_environment import ExperimentEnvironment
from .steps.experiment_runtime import ExperimentRuntime
from .steps import Step, SystemMetricsStep
from .ssh_manager import SSHManager


class Experiment:
    def __init__(self, steps: List[Step], runs: int):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._steps: List[Step] = steps
        self._runs: int = runs

    def _create_system_metric_step(self, resources: Path, system_meter_hosts: List[str]) -> Step:
        metric_file_entries = []
        for host in system_meter_hosts:
            metric_file_path = resources / "system.csv"
            metric_file_entries.append((host, metric_file_path))
        step = SystemMetricsStep(metric_file_entries)
        return step

    def _execute_steps(self, steps):
        self._logger.info("Execute %d steps", len(steps))
        for step in steps:
            self._logger.debug("execute step: %s", step.name)
            step.execute()

    def _run_experiment(self, steps, runtime, signal_handler):
        with ThreadPoolExecutor() as executor:
            futures = []
            try:
                self._logger.info("Starting all steps")
                for step in steps:
                    self._logger.debug("start step: %s", step.name)
                    future = step.start(executor)
                    if future:
                        futures.append(future)

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

            self._logger.info("Wait for threads")
            wait(futures, return_when=FIRST_EXCEPTION)
            for future in futures:
                if future.done():
                    future.result()

    def _run_experiment_runs(self, resources, steps, signal_handler, ssh_manager):
        system_meter_hosts: List[str] = []

        class Environment(ExperimentEnvironment):
            def get_resources_path(self) -> Path:
                return resources

            def add_shutdown_handler(self, handler: ShutdownHandler) -> None:
                signal_handler.add_shutdown_handler(handler)

            def register_for_system_meter(self, host: str) -> None:
                system_meter_hosts.append(host)

            def register_ssh_connection(self, user: str, host: str) -> None:
                ssh_manager.register_ssh_connection(user, host)

        environment = Environment()
        self._logger.info("Initialize all steps")
        for step in steps:
            self._logger.debug("init step: %s", step.name)
            step.init(environment)

        if system_meter_hosts:
            step = self._create_system_metric_step(resources, system_meter_hosts)
            steps.insert(0, step)
            self._logger.debug("init step: %s", step.name)
            step.init(environment)

        class Runtime(ExperimentRuntime):
            def get_ssh_connection(self, user: str, host: str) -> Connection:
                return ssh_manager.get_ssh_connection(user, host)

        runtime = Runtime()
        self._run_experiment(steps, runtime, signal_handler)

    def run(self, resources: Path):
        steps = self._steps[:]
        signal_handler = SignalHandler()
        runs_resources = resources / "runs"
        runs_resources.mkdir(parents=True, exist_ok=True)
        with SSHManager() as ssh_manager:
            for run in range(self._runs):
                run_resource = runs_resources / ("run_%03d" % run)
                run_resource.mkdir(parents=True, exist_ok=True)
                self._run_experiment_runs(run_resource, steps, signal_handler, ssh_manager)
