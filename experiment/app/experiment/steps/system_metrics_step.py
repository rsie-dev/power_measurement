import logging
import datetime
from threading import Event

from fabric import Connection
import ntplib
import humanize

from app.system_meter.measurement_logger import MeasurementLogger
from app.system_meter.metrics import SystemMeasurement
from .experiment_environment import ExperimentEnvironment
from .experiment_runtime import ExperimentRuntime
from .experiment_measurement import ExperimentMeasurement
from .experiment_resources import ExperimentResources
from .host_command_step import HostCommandStep
from .csv_metrics_logger import CSVMetricsLogger, MetricType


class StartupMonitor(MeasurementLogger):
    def __init__(self, _host_name: str, measurement: ExperimentMeasurement):
        self._host_name = _host_name
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

    def log(self, measurement: SystemMeasurement) -> None:
        self._startup_event.set()


class StartSystemMetricsClientStep(HostCommandStep):
    def __init__(self, host_name: str, host: str, ssh_user: str):
        super().__init__(host, ssh_user, [])
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host_name = host_name
        self._telegraf_server_address = None
        self._system_logger = None
        self._cpu_logger = None
        self._metrics_client_timeout: float = 10
        self._startup_monitor = None

    def prepare(self, environment: ExperimentEnvironment, measurement: ExperimentMeasurement,
                resources: ExperimentResources):
        super().prepare(environment, measurement, resources)

        self._startup_monitor = StartupMonitor(self._host_name, measurement)
        self._register_loggers(resources, measurement)
        telegraf_server = environment.get_metrics_server()
        self._telegraf_server_address = "%s:%d" % (telegraf_server[0], telegraf_server[1])
        # ToDo: log to resource folder?
        self._get_ntp_delta()

    def _register_loggers(self, resources: ExperimentResources, measurement: ExperimentMeasurement):
        metrics_resources_path = resources.metrics_resources_path()
        self._system_logger = CSVMetricsLogger(MetricType.SYSTEM, metrics_resources_path / "system.csv")
        self._cpu_logger = CSVMetricsLogger(MetricType.CPU, metrics_resources_path / "cpu.csv")
        measurement.register_for_system_meter(self._host_name, self._system_logger)
        measurement.register_for_system_meter(self._host_name, self._cpu_logger)

    def _get_ntp_delta(self):
        ntp_client = ntplib.NTPClient()
        self._logger.debug("get time diff to: %s", self._host)
        response = ntp_client.request(self._host, version=4)  # v4 is common
        offset_delta = datetime.timedelta(seconds = response.offset)
        status = "behind" if response.offset < 0 else "ahead"
        delta_str = humanize.precisedelta(offset_delta, minimum_unit="microseconds")
        self._logger.info("Host %s is %s %s", self._host, status, delta_str)
        return offset_delta

    def _execute_commands(self, connection: Connection):
        startup_event = self._startup_monitor.startup_event
        self._startup_monitor.start()
        self._logger.info("Start telegraf on: %s", self._host)
        connection.run("sudo systemctl start telegraf@%s" % self._telegraf_server_address, hide=True, pty=True)
        self._logger.info("Wait %s for telegraf client...", humanize.precisedelta(self._metrics_client_timeout))
        try:
            startup_event.wait(self._metrics_client_timeout)
        finally:
            self._startup_monitor.close()

    def _execute_stop_command(self, connection: Connection):
        self._logger.info("Stop telegraf on: %s", self._host)
        connection.run("sudo systemctl stop telegraf@%s" % self._telegraf_server_address, hide=True, pty=True)

    def stop(self, runtime: ExperimentRuntime, measurement: ExperimentMeasurement):
        connection = runtime.get_ssh_connection(self._ssh_user, self._host)
        try:
            self._execute_stop_command(connection)
        finally:
            if self._system_logger:
                measurement.unregister_for_system_meter(self._host_name, self._system_logger)
                self._system_logger.close()
            if self._cpu_logger:
                measurement.unregister_for_system_meter(self._host_name, self._cpu_logger)
                self._cpu_logger.close()
