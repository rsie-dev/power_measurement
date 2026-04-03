from abc import ABC, abstractmethod


class InitEnvironment(ABC):
    @abstractmethod
    def register_ssh_connection(self, user: str, host: str) -> None:
        pass


class ExperimentEnvironment(InitEnvironment):
    @abstractmethod
    def get_metrics_server(self) -> tuple[str, int]:
        pass
