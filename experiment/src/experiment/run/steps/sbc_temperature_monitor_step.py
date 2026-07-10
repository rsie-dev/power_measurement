import logging
from threading import Event, Condition
from concurrent.futures import Executor
import datetime
import json
from dataclasses import dataclass
from pathlib import Path

from fabric import Connection

from experiment.common import SSHHost
from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentRuntime
from experiment.run.base import ExperimentResources
from experiment.run.log import LogProvider
from experiment.run.log import LogDispatcher, TemperatureEntry

from .step import Step


class SBCTemperatureMonitorStep(Step):
    @dataclass(frozen=True)
    class Config:
        host: SSHHost
        sbc_temp_dispatcher: LogDispatcher[TemperatureEntry]
        log_provider: LogProvider
        path: str
        update_interval: float
        start_timeout: float = 3

    @dataclass
    class RunContext:
        path_tokens: list[str]
        resources_path: Path | None = None

    def __init__(self, config: Config):
        super().__init__("SBC temperature monitor")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config = config
        self._context = SBCTemperatureMonitorStep.RunContext(
            path_tokens=self._config.path.split("/"),
        )
        self._condition = Condition()
        self._stop = False

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources) -> None:
        environment.register_ssh_connection(self._config.host.ssh_user, self._config.host.host)
        self._context.resources_path = resources.resources_path()

    def start(self, runtime: ExperimentRuntime, executor: Executor) -> None:
        self._logger.debug("temperature monitor start")
        event = Event()
        connection = runtime.get_ssh_connection(self._config.host.ssh_user, self._config.host.host)
        executor.submit(self._run, connection, event)
        event.wait(self._config.start_timeout)

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
            with self._config.log_provider.start_log(self._context.resources_path):
                while True:
                    with self._condition:
                        while not self._stop:
                            if not self._condition.wait(timeout=self._config.update_interval):
                                self._collect_temperature(connection)

                        if self._stop:
                            break
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._logger.exception("Error: %s", e)
        finally:
            self._logger.debug("SBC temperature collector shut down")

    def _collect_temperature(self, connection: Connection):
        chip = self._context.path_tokens[0]
        result = connection.run(f"/usr/bin/sensors -J {chip}", shell="/usr/bin/sh", hide=True)
        sbc_temp = self._extract_sbc_temperature(result.stdout.strip())
        entry = TemperatureEntry(
            timestamp=datetime.datetime.now(datetime.UTC),
            temperature=sbc_temp,
        )
        self._config.sbc_temp_dispatcher.log(entry)

    def _extract_sbc_temperature(self, stdout: str) -> float:
        data = json.loads(stdout.strip())
        value = data
        for key in self._context.path_tokens:
            value = value[key]
        return float(value)
