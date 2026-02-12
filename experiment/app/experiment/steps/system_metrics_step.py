import logging
import datetime

from fabric import Connection
import ntplib
import humanize

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
        self._telegraf_server_address = None

    def prepare(self, environment: ExperimentEnvironment, measurement: ExperimentMeasurement,
                resources: ExperimentResources):
        super().prepare(environment, measurement, resources)
        measurement.register_for_system_meter(self._host_name)
        telegraf_server = environment.get_metrics_server()
        self._telegraf_server_address = "%s:%d" % (telegraf_server[0], telegraf_server[1])
        # ToDo: log to resource folder?
        self._get_ntp_delta()

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
        self._logger.info("Start telegraf on: %s", self._host)
        connection.run("sudo systemctl start telegraf@%s" % self._telegraf_server_address, hide=True, pty=True)

    def _execute_stop_command(self, connection: Connection):
        self._logger.info("Stop telegraf on: %s", self._host)
        connection.run("sudo systemctl stop telegraf@%s" % self._telegraf_server_address, hide=True, pty=True)

    def stop(self, runtime: ExperimentRuntime, measurement: ExperimentMeasurement):
        connection = runtime.get_ssh_connection(self._ssh_user, self._host)
        self._execute_stop_command(connection)
        measurement.unregister_for_system_meter(self._host_name)
