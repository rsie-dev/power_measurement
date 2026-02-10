import logging

from fabric import Connection

from .experiment_environment import ExperimentEnvironment
from .experiment_runtime import ExperimentRuntime
from .experiment_measurement import ExperimentMeasurement
from .host_command_step import HostCommandStep


class StartSystemMetricsClientStep(HostCommandStep):
    def __init__(self, host: str, host_name: str, ssh_user: str):
        super().__init__(host_name, ssh_user, [])
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host
        self._telegraf_server = None

    def init(self, environment: ExperimentEnvironment, measurement: ExperimentMeasurement):
        super().init(environment, measurement)
        measurement.register_for_system_meter(self._host)
        self._telegraf_server = environment.get_metrics_server()

    def _execute_commands(self, connection: Connection):
        self._logger.info("start telegraf on: %s", self._host_name)

        connection.run("sudo systemctl start telegraf@%s" % self._telegraf_server, hide=True, pty=True)

    def _execute_stop_command(self, connection: Connection):
        self._logger.info("stop telegraf on: %s", self._host_name)
        connection.run("sudo systemctl stop telegraf@%s" % self._telegraf_server, hide=True, pty=True)

    def stop(self, runtime: ExperimentRuntime, measurement: ExperimentMeasurement):
        connection = runtime.get_ssh_connection(self._ssh_user, self._host_name)
        self._execute_stop_command(connection)
        measurement.unregister_for_system_meter(self._host)
