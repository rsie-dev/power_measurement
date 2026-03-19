from abc import ABC, abstractmethod


class Command(ABC):
    @abstractmethod
    def execute(self, nr: int, connection, resources_path) -> None:
        pass
