from typing import TypeVar

from .logger import Logger

T = TypeVar('T')


class LogDispatcher(Logger[T]):
    def __init__(self):
        self._loggers: list[Logger[T]] = []

    def register_logger(self, logger: Logger[T]):
        self._loggers.append(logger)

    def unregister_logger(self, logger: Logger[T]):
        self._loggers.remove(logger)

    def log(self, data: T | list[T]) -> None:
        for logger in self._loggers:
            logger.log(data)
