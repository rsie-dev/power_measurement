import logging
from threading import Event
from concurrent.futures import Executor
from pathlib import Path
from typing import ContextManager
from contextlib import contextmanager
from contextlib import ExitStack

from fabric import Connection
import humanize

from app.system_meter import SystemMeasurement
from app.experiment.log import CSVMetricsLogger, MetricType, logger, Logger
from .experiment_environment import ExperimentEnvironment
from .experiment_runtime import ExperimentRuntime
from .experiment_measurement import ExperimentMeasurement
from .experiment_resources import ExperimentResources
from .host_command_step import BaseHostCommandStep
from .log_provider import LogProvider
from .host import SSHHost


class StartupMonitor(Logger[SystemMeasurement]):
    def __init__(self, host_name: str, measurement: ExperimentMeasurement):
        self._host_name = host_name
        self._measurement = measurement
        self._startup_event = Event()

    @property
    def startup_event(self):
        return self._startup_event

    def init(self) -> None:
        pass

    def start(self) -> None:
        self._measurement.register_for_system_meter(self._host_name, self)

    def close(self):
        self._measurement.unregister_for_system_meter(self._host_name, self)

    def log(self, measurement: SystemMeasurement | list[SystemMeasurement]) -> None:
        self._startup_event.set()


class SystemMetricsClientStep(BaseHostCommandStep, LogProvider):
    def __init__(self, formatter: logging.Formatter, host: SSHHost):
        super().__init__("system metrics", host)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._formatter = formatter
        self._telegraf_server_address = None
        self._metrics_client_timeout: float = 5
        self._startup_monitor = None
        self._measurement = None

    @contextmanager
    def start_log(self, resource_path: Path) -> ContextManager:
        @contextmanager
        def log_registrar(log):
            with logger(log) as data_logger:
                try:
                    self._measurement.register_for_system_meter(self._host.host_name, data_logger)
                    yield data_logger
                finally:
                    self._measurement.unregister_for_system_meter(self._host.host_name, data_logger)

        with ExitStack() as stack:
            system_logger = CSVMetricsLogger(MetricType.SYSTEM, resource_path / "system.csv", self._formatter)
            stack.enter_context(log_registrar(system_logger))

            cpu_logger = CSVMetricsLogger(MetricType.CPU, resource_path / "cpu.csv", self._formatter)
            stack.enter_context(log_registrar(cpu_logger))

            yield stack

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources):
        super().prepare(environment, resources)
        telegraf_server = environment.get_metrics_server()
        self._telegraf_server_address = "%s:%d" % (telegraf_server[0], telegraf_server[1])

    def _execute_commands(self, connection: Connection):
        startup_event = self._startup_monitor.startup_event
        self._startup_monitor.start()
        self._logger.info("Start telegraf on: %s", self._host.host)
        connection.run("sudo systemctl start telegraf@%s" % self._telegraf_server_address, hide=True, pty=True)
        self._logger.info("Wait %s for telegraf client...", humanize.precisedelta(self._metrics_client_timeout))
        try:
            startup_event.wait(self._metrics_client_timeout)
        finally:
            self._startup_monitor.close()

    def _execute_stop_command(self, connection: Connection):
        self._logger.info("Stop telegraf on: %s", self._host.host)
        connection.run("sudo systemctl stop telegraf@%s" % self._telegraf_server_address, hide=True, pty=True)

    def start(self, executor: Executor, measurement: ExperimentMeasurement) -> None:
        self._startup_monitor = StartupMonitor(self._host.host_name, measurement)
        self._measurement = measurement

    def stop(self, runtime: ExperimentRuntime, measurement: ExperimentMeasurement):
        connection = runtime.get_ssh_connection(self._host.ssh_user, self._host.host)
        self._execute_stop_command(connection)
