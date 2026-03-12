import logging

from app.experiment.base import InitEnvironment
from app.experiment.base import ExperimentRuntime
from .step import InitStep
from .host import SSHHost


class HostnameValidationStep(InitStep):
    def __init__(self, host: SSHHost):
        super().__init__("hostname validation")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host

    def init(self, environment: InitEnvironment) -> None:
        environment.register_ssh_connection(self._host.ssh_user, self._host.host)

    def execute(self, runtime: ExperimentRuntime) -> None:
        connection = runtime.get_ssh_connection(self._host.ssh_user, self._host.host)
        result = connection.run('hostname', hide=True)
        device_hostname = result.stdout.strip()
        if device_hostname != self._host.host_name:
            raise AssertionError(f"invalid hostname: {device_hostname} expected: {self._host.host_name}")
