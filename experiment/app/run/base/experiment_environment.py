from abc import ABC, abstractmethod

from app.common import ShutdownHandler


class InitEnvironment(ABC):
    @abstractmethod
    def register_ssh_connection(self, user: str, host: str) -> None:
        pass


class ExperimentEnvironment(InitEnvironment):
    @abstractmethod
    def get_metrics_server(self) -> tuple[str, int]:
        pass

    @abstractmethod
    def add_shutdown_handler(self, handler: ShutdownHandler) -> None:
        pass

    @abstractmethod
    def remove_shutdown_handler(self, handler: ShutdownHandler) -> None:
        pass
