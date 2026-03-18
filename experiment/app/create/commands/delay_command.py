import logging
import time

from app.api import Command


class DelayCommand(Command):
    def __init__(self, delay: int, kind: str):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._delay = delay
        self._kind = kind

    def execute(self, connection, resources_path) -> None:
        kind = self._kind[:1].upper() + self._kind[1:]
        self._logger.info("%s delay: %ss", kind, self._delay)
        time.sleep(self._delay)
