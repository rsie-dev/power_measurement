import logging
from threading import Event, Condition
from concurrent.futures import Executor

from fabric import Connection

from experiment.common import SSHHost
from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentRuntime
from experiment.run.base import ExperimentResources

from .step import Step


class SBCTemperatureMonitorStep(Step):
    def __init__(self, host: SSHHost):
        super().__init__("SBC temperature monitor")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host
        self._condition = Condition()
        self._stop = False
        self._start_timeout = 3
        self._update_interval = 1

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources) -> None:
        environment.register_ssh_connection(self._host.ssh_user, self._host.host)

    def start(self, runtime: ExperimentRuntime, executor: Executor) -> None:
        self._logger.debug("temperature monitor start")
        event = Event()
        connection = runtime.get_ssh_connection(self._host.ssh_user, self._host.host)
        executor.submit(self._run, connection, event)
        event.wait(self._start_timeout)

    def stop(self, runtime: ExperimentRuntime) -> None:
        self._logger.debug("Signal SBC temperature collector to shutdown")
        with self._condition:
            self._stop = True
            self._condition.notify()

    def execute(self, runtime: ExperimentRuntime) -> None:
        pass

    def _run(self, connection: Connection, event: Event) -> None:
        self._logger.debug("SBC temperature collector start")
        try:
            event.set()
            while True:
                with self._condition:
                    while not self._stop:
                        if not self._condition.wait(timeout=self._update_interval):
                            self._collect_temperature(connection)

                    if self._stop:
                        break
        finally:
            self._logger.debug("SBC temperature collector shut down")

    def _collect_temperature(self, connection: Connection):
        self._logger.warning("collecting SBC temp")
        result = connection.run('uname -s')
        self._logger.warning("got: %s", result.stdout.strip())
