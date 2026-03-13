from fabric import Connection

from app.experiment.base import ExperimentRuntime
from app.ssh import SSHManager


class Runtime(ExperimentRuntime):
    def __init__(self, ssh_manager: SSHManager):
        self._ssh_manager = ssh_manager

    @property
    def ssh_manager(self):
        return self._ssh_manager

    def get_ssh_connection(self, user: str, host: str) -> Connection:
        return self._ssh_manager.get_ssh_connection(user, host)
