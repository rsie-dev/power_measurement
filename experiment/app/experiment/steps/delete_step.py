import logging

from app.common import SSHHost
from app.experiment.base import ExperimentEnvironment
from app.experiment.base import ExperimentRuntime
from app.experiment.base import ExperimentResources

from .step import Step


class DeleteStep(Step):
    def __init__(self, host: SSHHost, remote: str):
        super().__init__("delete")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host
        self._remote = remote

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources):
        environment.register_ssh_connection(self._host.ssh_user, self._host.host)

    def execute(self, runtime: ExperimentRuntime):
        self._logger.info("Delete remote file: %s", self._remote)
        connection = runtime.get_ssh_connection(self._host.ssh_user, self._host.host)
        command = f"rm {self._remote}"
        connection.run(command, hide=True)
