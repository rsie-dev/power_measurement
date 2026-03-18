from abc import ABC, abstractmethod
from pathlib import Path
from typing import ContextManager, TypeVar, Generic, Callable
from contextlib import contextmanager

from .base_logger import BaseLogger, logger
from .log_dispatcher import LogDispatcher


class LogProvider(ABC):
    @abstractmethod
    def start_log(self, resource_path: Path) -> ContextManager:
        pass


T = TypeVar('T')
LoggerFactory = Callable[[Path], BaseLogger]


class GenericLogProvider(LogProvider, Generic[T]):
    def __init__(self, log_dispatcher: LogDispatcher[T], log_factory: LoggerFactory):
        self._log_dispatcher = log_dispatcher
        self._log_factory = log_factory

    @contextmanager
    def start_log(self, resource_path: Path) -> ContextManager:
        base_logger = self._log_factory(resource_path)
        with logger(base_logger) as data_logger:
            self._log_dispatcher.register_logger(data_logger)
            try:
                yield data_logger
            finally:
                self._log_dispatcher.unregister_logger(data_logger)
