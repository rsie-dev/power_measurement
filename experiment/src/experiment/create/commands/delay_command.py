import logging
import time
from datetime import timedelta

import humanize

from experiment.api import Command


class DelayCommand(Command):
    def __init__(self, delay: timedelta, kind: str):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._delay = delay
        self._kind = kind

    def execute(self, nr: int, connection) -> None:
        kind = self._kind[:1].upper() + self._kind[1:]
        self._logger.info("%s delay: %s", kind, humanize.naturaldelta(self._delay))
        self._sleep(self._delay)

    def _sleep(self, timeout: timedelta):
        deadline = time.monotonic() + timeout.total_seconds()
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            time.sleep(remaining)
