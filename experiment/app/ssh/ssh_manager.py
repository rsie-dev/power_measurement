from abc import ABC, abstractmethod

from fabric import Connection


class SSHManager(ABC):
    @abstractmethod
    def register_ssh_connection(self, user: str, host: str) -> None:
        pass

    @abstractmethod
    def get_ssh_connection(self, user: str, host: str) -> Connection:
        pass
