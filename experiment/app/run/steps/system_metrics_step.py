import logging
from threading import Event

from fabric import Connection
import humanize

from app.common import SSHHost
from app.system_meter import SystemMeasurement
from app.run.log import Logger, LogDispatcher
from app.run.base import ExperimentEnvironment
from app.run.base import ExperimentRuntime
from app.run.base import ExperimentResources
from .host_command_step import BaseHostCommandStep


class StartupMonitor(Logger[SystemMeasurement]):
    def __init__(self, host_name: str, metrics_dispatcher: LogDispatcher[SystemMeasurement]):
        self._host_name = host_name
        self._metrics_dispatcher = metrics_dispatcher
        self._startup_event = Event()

    @property
    def startup_event(self):
        return self._startup_event

    def __enter__(self):
        self._metrics_dispatcher.register_logger(self)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._metrics_dispatcher.unregister_logger(self)

    def log(self, data: SystemMeasurement | list[SystemMeasurement]) -> None:
        self._startup_event.set()


class SystemMetricsClientStep(BaseHostCommandStep):
    def __init__(self, host: SSHHost, metrics_dispatcher: LogDispatcher[SystemMeasurement]):
        super().__init__("system metrics", host)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._telegraf_server_address = None
        self._metrics_client_timeout: float = 5
        self._metrics_dispatcher = metrics_dispatcher

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources):
        super().prepare(environment, resources)
        telegraf_server = environment.get_metrics_server()
        self._telegraf_server_address = "%s:%d" % (telegraf_server[0], telegraf_server[1])

    def _execute_commands(self, connection: Connection):
        with StartupMonitor(self._host.host_name, self._metrics_dispatcher) as startup_monitor:
            startup_event = startup_monitor.startup_event
            self._execute_start_command(connection)
            self._logger.info("Wait %s for telegraf client...", humanize.precisedelta(self._metrics_client_timeout))
            startup_event.wait(self._metrics_client_timeout)
            self._logger.info("Telegraf client connected")

    def stop(self, runtime: ExperimentRuntime):
        connection = runtime.get_ssh_connection(self._host.ssh_user, self._host.host)
        self._execute_stop_command(connection)

    def _execute_start_command(self, connection: Connection):
        self._logger.info("Start telegraf on: %s", self._host.host)
        connection.sudo("systemctl start telegraf@%s.service" % self._telegraf_server_address, hide=True)

    def _execute_stop_command(self, connection: Connection):
        self._logger.info("Stop telegraf on: %s", self._host.host)
        connection.sudo("systemctl stop telegraf@%s.service" % self._telegraf_server_address, hide=True)
