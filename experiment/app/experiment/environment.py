from pathlib import Path

from app.common import SignalHandler
from app.common import ShutdownHandler
from .steps.experiment_environment import ExperimentEnvironment
from .ssh_manager import SSHManager


class Environment(ExperimentEnvironment):
    def __init__(self, ssh_manager: SSHManager, signal_handler: SignalHandler,
                 resource_path: Path, metrics_server):
        self._ssh_manager = ssh_manager
        self._signal_handler = signal_handler
        self._resource_path = resource_path
        self._metrics_server: str = metrics_server

    def get_metrics_server(self) -> str:
        return self._metrics_server

    def get_resources_path(self) -> Path:
        return self._resource_path

    def add_shutdown_handler(self, handler: ShutdownHandler) -> None:
        self._signal_handler.add_shutdown_handler(handler)

    def register_ssh_connection(self, user: str, host: str) -> None:
        self._ssh_manager.register_ssh_connection(user, host)
