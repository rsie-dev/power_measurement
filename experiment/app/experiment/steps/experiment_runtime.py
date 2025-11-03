from abc import ABC, abstractmethod

from fabric import Connection


class ExperimentRuntime(ABC):
    @abstractmethod
    def get_ssh_connection(self, user: str, host: str) -> Connection:
        pass

    @abstractmethod
    def unregister_for_system_meter(self, host: str) -> None:
        pass
