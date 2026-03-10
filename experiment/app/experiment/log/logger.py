from typing import TypeVar, Generic
from abc import abstractmethod

T = TypeVar('T')


class Logger(Generic[T]):
    @abstractmethod
    def log(self, data: T | list[T]) -> None:
        pass
