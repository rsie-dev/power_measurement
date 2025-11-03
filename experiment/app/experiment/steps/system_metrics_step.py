import logging
import threading
from concurrent.futures import Executor

from fabric import Connection

from app.experiment.measurement_dispatcher import MeasurementDispatcher
from app.system_meter import MetricsServer
from .step import Step, ExperimentEnvironment
from .host_command_step import HostCommandStep
from .csv_system_logger import CSVSystemLogger


class RegisterForSystemMetricsStep(Step):
    def __init__(self, host: str):
        super().__init__("register for system meter")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host

    def init(self, environment: ExperimentEnvironment):
        environment.register_for_system_meter(self._host)


class StartSystemMetricsClientStep(HostCommandStep):
    def __init__(self, host_name: str, ssh_user: str):
        super().__init__(host_name, ssh_user, [])
        self._logger = logging.getLogger(self.__class__.__name__)

    def _execute_commands(self, connection: Connection):
        self._logger.info("start telegraf on: %s", self._host_name)
        connection.run("sudo systemctl start telegraf", hide=True, pty=True)

    def _execute_stop_command(self, connection: Connection):
        self._logger.info("stop telegraf on: %s", self._host_name)
        connection.run("sudo systemctl stop telegraf", hide=True, pty=True)

    def stop(self):
        with self._create_connection() as con:
            self._execute_stop_command(con)


class SystemMetricsStep(Step):
    def __init__(self, metric_file_entries):
        super().__init__("system metrics")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._metric_file_entries = metric_file_entries
        self._metrics_server = MetricsServer()
        self._start_timeout = 3

    def init(self, environment: ExperimentEnvironment):
        environment.add_shutdown_handler(self._metrics_server)

    def _system_collector(self, server_host: str, server_port: int, metric_file_entries, event):
        def on_startup():
            self._logger.debug("REST system_meter running")
            event.set()

        self._logger.debug("REST system_meter start")
        try:
            with MeasurementDispatcher() as dl:
                for host_name, resource_path in metric_file_entries:
                    dl.enter_host_context(host_name, CSVSystemLogger(resource_path))
                self._metrics_server.run(server_host, server_port, dl, on_startup)
        finally:
            self._logger.debug("REST system_meter shut down")

    def start(self, executor: Executor):
        event = threading.Event()
        future = executor.submit(self._system_collector, "192.168.1.201", 10000, self._metric_file_entries, event)
        event.wait(self._start_timeout)
        return future

    def stop(self):
        self._metrics_server.shut_down(False)
