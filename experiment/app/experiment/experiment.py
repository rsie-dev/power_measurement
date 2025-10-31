import logging
from typing import List
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_EXCEPTION

from app.run.signal_handler import SignalHandler
from app.system_meter import ShutdownHandler
from .steps import Step, SystemMetricsStep
from .experiment_environment import ExperimentEnvironment


class Experiment:
    def __init__(self, steps: List[Step]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._steps = steps

    def _get_steps(self):
        return self._steps[:]

    def run(self, resources: Path, signal_handler: SignalHandler):
        system_meter_hosts: List[str] = []

        class Environment(ExperimentEnvironment):
            def get_resources_path(self):
                return resources

            def add_shutdown_handler(self, handler: ShutdownHandler):
                signal_handler.add_shutdown_handler(handler)

            def register_for_system_meter(self, host: str) -> None:
                system_meter_hosts.append(host)

        environment = Environment()
        steps = self._get_steps()
        for step in steps:
            self._logger.debug("init step: %s", step.name)
            step.init(environment)

        if system_meter_hosts:
            metric_file_entries = []
            for host in system_meter_hosts:
                metric_file_path = resources / "system.csv"
                metric_file_entries.append((host, metric_file_path))
            step = SystemMetricsStep(metric_file_entries)
            steps.insert(0, step)
            self._logger.debug("init step: %s", step.name)
            step.init(environment)

        with ThreadPoolExecutor() as executor:
            futures = []
            for step in steps:
                self._logger.debug("start step: %s", step.name)
                future = step.start(executor)
                if future:
                    futures.append(future)

            for step in steps:
                self._logger.debug("execute step: %s", step.name)
                step.execute()

            for step in steps:
                self._logger.debug("stop step: %s", step.name)
                step.stop()

            self._logger.debug("wait for threads")
            wait(futures, return_when=FIRST_EXCEPTION)
            for future in futures:
                if future.done():
                    future.result()
        self._logger.debug("executor shut down")
