from abc import ABC, abstractmethod

from fabric import Connection

from .host_info import HostInfo


class ConnectionFactory(ABC):
    @abstractmethod
    def register_ssh_connection(self, host_info: HostInfo) -> None:
        pass

    @abstractmethod
    def create_connection(self, host_info: HostInfo) -> Connection:
        pass
