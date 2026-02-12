from app.common import SignalHandler
from app.common import ShutdownHandler
from .steps.experiment_environment import ExperimentEnvironment, InitEnvironment
from .ssh_manager import SSHManager


class InitialEnvironment(InitEnvironment):
    def __init__(self, ssh_manager: SSHManager):
        self._ssh_manager = ssh_manager

    def register_ssh_connection(self, user: str, host: str) -> None:
        self._ssh_manager.register_ssh_connection(user, host)


class Environment(InitialEnvironment, ExperimentEnvironment):
    def __init__(self, ssh_manager: SSHManager, signal_handler: SignalHandler, metrics_server):
        super().__init__(ssh_manager)
        self._signal_handler = signal_handler
        self._metrics_server: str = metrics_server

    def get_metrics_server(self) -> str:
        return self._metrics_server

    def add_shutdown_handler(self, handler: ShutdownHandler) -> None:
        self._signal_handler.add_shutdown_handler(handler)
