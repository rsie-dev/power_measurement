from fabric import Connection

from .steps.experiment_runtime import ExperimentRuntime
from .ssh_manager import SSHManager
from .measurement_dispatcher import MeasurementDispatcher


class Runtime(ExperimentRuntime):
    def __init__(self, ssh_manager: SSHManager, measurement_dispatcher: MeasurementDispatcher):
        self._ssh_manager = ssh_manager
        self._measurement_dispatcher = measurement_dispatcher

    @property
    def ssh_manager(self) -> SSHManager:
        return self._ssh_manager

    def get_ssh_connection(self, user: str, host: str) -> Connection:
        return self._ssh_manager.get_ssh_connection(user, host)

    def unregister_for_system_meter(self, host: str) -> None:
        logger = self._measurement_dispatcher.remove_logger(host)
        if logger:
            logger.close()
