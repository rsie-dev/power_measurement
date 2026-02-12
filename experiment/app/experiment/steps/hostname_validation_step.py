import logging
from .step import InitStep

from .experiment_runtime import ExperimentRuntime
from .experiment_environment import InitEnvironment


class HostnameValidationStep(InitStep):
    def __init__(self, host_name: str, host: str, ssh_user: str):
        super().__init__("hostname validation")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host_name = host_name
        self._host = host
        self._ssh_user = ssh_user

    def init(self, environment: InitEnvironment) -> None:
        environment.register_ssh_connection(self._ssh_user, self._host)

    def execute(self, runtime: ExperimentRuntime) -> None:
        connection = runtime.get_ssh_connection(self._ssh_user, self._host)
        result = connection.run('hostname', hide=True)
        device_hostname = result.stdout.strip()
        if device_hostname != self._host_name:
            raise AssertionError(f"invalid hostname: {device_hostname} expected: {self._host_name}")
