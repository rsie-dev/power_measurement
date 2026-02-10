from abc import ABC, abstractmethod

from app.common import ShutdownHandler


class ExperimentEnvironment(ABC):
    @abstractmethod
    def get_metrics_server(self) -> str:
        pass

    @abstractmethod
    def add_shutdown_handler(self, handler: ShutdownHandler) -> None:
        pass

    @abstractmethod
    def register_ssh_connection(self, user: str, host: str) -> None:
        pass
