from pathlib import Path

from app.common import SignalHandler
from app.common import ShutdownHandler
from .steps.csv_system_logger import CSVSystemLogger
from .steps.experiment_environment import ExperimentEnvironment
from .ssh_manager import SSHManager
from .measurement_dispatcher import MeasurementDispatcher


class Environment(ExperimentEnvironment):
    def __init__(self, ssh_manager: SSHManager, signal_handler: SignalHandler,
                 measurement_dispatcher: MeasurementDispatcher, resource_path: Path,
                 metrics_server_host: str, metrics_server_port: int):
        self._ssh_manager = ssh_manager
        self._signal_handler = signal_handler
        self._measurement_dispatcher = measurement_dispatcher
        self._resource_path = resource_path
        self._metrics_server_host: str = metrics_server_host
        self._metrics_server_port: int = metrics_server_port

    def get_metrics_server(self) -> str:
        return "%s:%s" % (self._metrics_server_host, self._metrics_server_port)

    def get_resources_path(self) -> Path:
        return self._resource_path

    def add_shutdown_handler(self, handler: ShutdownHandler) -> None:
        self._signal_handler.add_shutdown_handler(handler)

    def register_for_system_meter(self, host: str) -> None:
        metric_file_path = self.get_resources_path() / "system.csv"
        self._measurement_dispatcher.add_logger(host, CSVSystemLogger(metric_file_path))

    def register_ssh_connection(self, user: str, host: str) -> None:
        self._ssh_manager.register_ssh_connection(user, host)
