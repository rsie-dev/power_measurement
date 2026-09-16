from typing import TypeVar
from threading import RLock

from .logger import Logger

T = TypeVar('T')


class LogDispatcher(Logger[T]):
    def __init__(self):
        self._loggers: list[Logger[T]] = []
        self._lock = RLock()

    def register_logger(self, logger: Logger[T]):
        with self._lock:
            self._loggers.append(logger)

    def unregister_logger(self, logger: Logger[T]):
        with self._lock:
            self._loggers.remove(logger)

    def log(self, data: T | list[T]) -> None:
        with self._lock:
            loggers = self._loggers[:]

        for logger in loggers:
            logger.log(data)
