import logging
from pathlib import Path

from app.common import SSHHost
from app.experiment.base import ExperimentEnvironment
from app.experiment.base import ExperimentRuntime
from app.experiment.base import ExperimentResources

from .step import Step


class UploadStep(Step):
    def __init__(self, host: SSHHost, local: Path, remote: Path):
        super().__init__("upload")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host
        self._local = local
        self._remote = remote

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources):
        environment.register_ssh_connection(self._host.ssh_user, self._host.host)

    def execute(self, runtime: ExperimentRuntime):
        self._logger.info("Upload local file: %s to %s:%s", self._local, self._host.host, self._remote)
        connection = runtime.get_ssh_connection(self._host.ssh_user, self._host.host)
        connection.put(local=str(self._local), remote=str(self._remote))
