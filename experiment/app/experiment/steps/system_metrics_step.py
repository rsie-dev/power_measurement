import logging
import datetime

from fabric import Connection
import ntplib

from .experiment_environment import ExperimentEnvironment
from .experiment_runtime import ExperimentRuntime
from .experiment_measurement import ExperimentMeasurement
from .experiment_resources import ExperimentResources
from .host_command_step import HostCommandStep


class StartSystemMetricsClientStep(HostCommandStep):
    def __init__(self, host_name: str, host: str, ssh_user: str):
        super().__init__(host, ssh_user, [])
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host_name = host_name
        self._telegraf_server = None

    def init(self, environment: ExperimentEnvironment, measurement: ExperimentMeasurement,
             resources: ExperimentResources):
        super().init(environment, measurement, resources)
        measurement.register_for_system_meter(self._host_name)
        self._telegraf_server = environment.get_metrics_server()
        self._get_ntp_delta()

    def _get_ntp_delta(self):
        ntp_client = ntplib.NTPClient()
        self._logger.debug("get time diff to: %s", self._host)
        resp = ntp_client.request(self._host, version=4)  # v4 is common
        dt = datetime.datetime.fromtimestamp(resp.tx_time)
        self._logger.info("Time diff to: %s = %s (%s)", self._host, resp.offset, dt)

    def _execute_commands(self, connection: Connection):
        self._logger.info("Start telegraf on: %s", self._host_name)

        connection.run("sudo systemctl start telegraf@%s" % self._telegraf_server, hide=True, pty=True)

    def _execute_stop_command(self, connection: Connection):
        self._logger.info("Stop telegraf on: %s", self._host_name)
        connection.run("sudo systemctl stop telegraf@%s" % self._telegraf_server, hide=True, pty=True)

    def stop(self, runtime: ExperimentRuntime, measurement: ExperimentMeasurement):
        connection = runtime.get_ssh_connection(self._ssh_user, self._host)
        self._execute_stop_command(connection)
        measurement.unregister_for_system_meter(self._host_name)
