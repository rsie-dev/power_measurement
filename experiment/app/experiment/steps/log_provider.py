from abc import ABC, abstractmethod
from pathlib import Path
from typing import ContextManager


class LogProvider(ABC):
    @abstractmethod
    def start_log(self, resource_path: Path) -> ContextManager:
        pass
