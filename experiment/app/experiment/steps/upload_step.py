import logging

from .experiment_environment import ExperimentEnvironment
from .experiment_runtime import ExperimentRuntime
from .experiment_resources import ExperimentResources

from .step import Step
from .host import SSHHost


class UploadStep(Step):
    def __init__(self, host: SSHHost, local: str, remote: str):
        super().__init__("upload")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host
        self._local = local
        self._remote = remote

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources):
        environment.register_ssh_connection(self._host.ssh_user, self._host.host)

    def execute(self, runtime: ExperimentRuntime):
        self._logger.info("Upload local file: %s to remote: %s", self._local, self._remote)
        connection = runtime.get_ssh_connection(self._host.ssh_user, self._host.host)
        connection.put(local=self._local, remote=self._remote)
