import logging
from threading import Event, Condition
from concurrent.futures import Executor, wait, FIRST_EXCEPTION
import datetime
from dataclasses import dataclass
from pathlib import Path
import time

from fabric import Connection

from experiment.common import SSHHost
from experiment.common import MeasurementAbort
from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentRuntime
from experiment.run.base import ExperimentResources
from experiment.run.log import LogProvider
from experiment.run.log import LogDispatcher, TemperatureEntry

from .step import Step


class SBCTemperatureMonitorStep(Step, MeasurementAbort):
    SENSOR_NAMES = [
        "cpu_thermal",  # raspberry pi 5
        "coretemp",     # radxa x4
        "sfctemp"       # visionfive 2
    ]

    @dataclass(frozen=True)
    class Config:
        host: SSHHost
        sbc_temp_dispatcher: LogDispatcher[TemperatureEntry]
        log_provider: LogProvider
        update_interval: float
        start_timeout: float = 3

    @dataclass
    class RunContext:
        resources_path: Path | None = None
        abort_reason: Exception | None = None

    def __init__(self, config: Config):
        super().__init__("SBC temperature monitor")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._config = config
        self._context = SBCTemperatureMonitorStep.RunContext()
        self._condition = Condition()
        self._stop = False
        self._future = None

    def get_abort_reason(self) -> Exception | None:
        return self._context.abort_reason

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources) -> None:
        environment.register_ssh_connection(self._config.host.ssh_user, self._config.host.host)
        self._context.resources_path = resources.resources_path()

    def start(self, runtime: ExperimentRuntime, executor: Executor) -> None:
        self._logger.debug("temperature monitor start")
        event = Event()
        connection = runtime.get_ssh_connection(self._config.host.ssh_user, self._config.host.host)
        kernel_temperature_file = self._find_kernel_temperature_file(connection)
        if not kernel_temperature_file:
            raise RuntimeError("unable to find kernel SBC temperature file")
        self._logger.debug("found kernel temperature file: %s", kernel_temperature_file)
        future =executor.submit(self._run, connection, event, kernel_temperature_file)
        if not event.wait(self._config.start_timeout):
            raise TimeoutError(f"SBC monitor thread did not start within {self._config.start_timeout} seconds")
        self._future = future

    def _find_kernel_temperature_file(self, connection: Connection) -> Path | None:
        hwmon_folder = Path("/sys/class/hwmon")
        self._logger.debug("searching for sbc temperature file")
        result = connection.run(f"ls -1 {hwmon_folder}", hide=True)
        entries = result.stdout.splitlines()
        entries.sort()
        for entry in entries:
            name_path = hwmon_folder / entry / "name"
            name = self._read_remote_file(connection, name_path).strip()
            self._logger.debug("entry %s = %s", name_path, name)
            if name in self.SENSOR_NAMES:
                return hwmon_folder / entry / "temp1_input"
        return None

    def stop(self, runtime: ExperimentRuntime) -> None:
        self._logger.debug("Signal SBC temperature collector to shutdown")
        with self._condition:
            self._stop = True
            self._condition.notify()

        if self._future:
            wait([self._future], return_when=FIRST_EXCEPTION)
            self._future.result()

    def execute(self, runtime: ExperimentRuntime) -> None:
        pass

    def _run(self, connection: Connection, event: Event, kernel_temperature_file: Path) -> None:
        self._logger.debug("SBC temperature collector start")
        try:
            event.set()
            with self._config.log_provider.start_log(self._context.resources_path):
                self._collect_loop(connection, kernel_temperature_file)
        except Exception as e:  # pylint: disable=broad-exception-caught
            self._logger.fatal("%s -> abort", e)
            self._context.abort_reason = e
        finally:
            self._logger.debug("SBC temperature collector shut down")

    def _collect_loop(self, connection: Connection, kernel_temperature_file: Path) -> None:
        next_run = time.monotonic()
        while True:
            next_run += self._config.update_interval
            with self._condition:
                while True:
                    timeout = next_run - time.monotonic()
                    if timeout <= 0:
                        break
                    self._condition.wait(timeout=timeout)
                    if self._stop:
                        return
            self._collect_temperature(connection, kernel_temperature_file)

    def _collect_temperature(self, connection: Connection, kernel_temperature_file: Path):
        str_value = self._read_remote_file(connection, kernel_temperature_file).strip()
        sbc_temp = float(str_value) / 1000.0
        entry = TemperatureEntry(
            timestamp=datetime.datetime.now(datetime.UTC),
            temperature=sbc_temp,
        )
        self._config.sbc_temp_dispatcher.log(entry)

    def _read_remote_file(self, connection: Connection, remote_file: Path) -> str:
        result = connection.run(f"cat {remote_file}", shell="/usr/bin/sh", hide=True)
        content = result.stdout
        return content
