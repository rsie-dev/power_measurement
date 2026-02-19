from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def execute(self, connection, resources_path) -> None:
        pass
