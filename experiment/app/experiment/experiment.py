import logging
from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_EXCEPTION
from getpass import getpass

from app.common import SignalHandler
from app.common import ShutdownHandler
from .steps.experiment_environment import ExperimentEnvironment
from .steps import Step, SystemMetricsStep


class Experiment:
    def __init__(self, steps: List[Step]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._steps = steps

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

    def _run_experiment(self, steps, signal_handler):
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
                            step.execute()
                except KeyboardInterrupt:
                    pass

            finally:
                self._logger.info("Stopping all steps")
                for step in list(reversed(steps)):
                    self._logger.debug("stop step: %s", step.name)
                    step.stop()

            self._logger.info("Wait for threads")
            wait(futures, return_when=FIRST_EXCEPTION)
            for future in futures:
                if future.done():
                    future.result()

    def run(self, resources: Path):
        system_meter_hosts: List[str] = []
        signal_handler = SignalHandler()

        class Environment(ExperimentEnvironment):
            def get_resources_path(self):
                return resources

            def add_shutdown_handler(self, handler: ShutdownHandler):
                signal_handler.add_shutdown_handler(handler)

            def register_for_system_meter(self, host: str) -> None:
                system_meter_hosts.append(host)

            def get_password(self, user: str, host: str) -> str:
                return getpass(f'SSH password for {user}@{host}: ')

        environment = Environment()
        steps = self._steps[:]
        self._logger.info("Initialize all steps")
        for step in steps:
            self._logger.debug("init step: %s", step.name)
            step.init(environment)

        if system_meter_hosts:
            step = self._create_system_metric_step(resources, system_meter_hosts)
            steps.insert(0, step)
            self._logger.debug("init step: %s", step.name)
            step.init(environment)

        self._run_experiment(steps, signal_handler)
