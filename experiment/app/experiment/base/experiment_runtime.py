from abc import ABC, abstractmethod

from fabric import Connection


class ExperimentRuntime(ABC):
    @abstractmethod
    def get_ssh_connection(self, user: str, host: str) -> Connection:
        pass
