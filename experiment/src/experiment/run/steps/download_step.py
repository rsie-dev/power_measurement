import logging
from pathlib import Path

from experiment.common import SSHHost
from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentRuntime
from experiment.run.base import ExperimentResources

from .step import Step


class DownloadStep(Step):
    def __init__(self, host: SSHHost, remote: Path, local: Path):
        super().__init__("download")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host
        self._remote = remote
        self._local = local

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources):
        environment.register_ssh_connection(self._host.ssh_user, self._host.host)

    def execute(self, runtime: ExperimentRuntime):
        self._logger.info("Download remote file: %s:%s to %s", self._host.host, self._remote, self._local)
        connection = runtime.get_ssh_connection(self._host.ssh_user, self._host.host)
        if self._local.is_dir():
            local = str(self._local) + "/"
        else:
            local = str(self._local)
        connection.get(remote=str(self._remote), local=local)
