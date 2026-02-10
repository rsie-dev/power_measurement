from abc import ABC, abstractmethod
from pathlib import Path

from app.common import ShutdownHandler


class ExperimentEnvironment(ABC):
    @abstractmethod
    def get_metrics_server(self) -> str:
        pass

    @abstractmethod
    def get_resources_path(self) -> Path:
        pass

    @abstractmethod
    def add_shutdown_handler(self, handler: ShutdownHandler) -> None:
        pass

    @abstractmethod
    def register_for_system_meter(self, host: str) -> None:
        pass

    @abstractmethod
    def register_ssh_connection(self, user: str, host: str) -> None:
        pass
