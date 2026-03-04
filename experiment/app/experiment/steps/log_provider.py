from abc import ABC, abstractmethod
from pathlib import Path


class LogProvider(ABC):
    @abstractmethod
    def start_log(self, resource_path: Path):
        pass

    @abstractmethod
    def stop_log(self):
        pass
