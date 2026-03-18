import logging
from threading import Event
from collections import deque

from app.run.log import LogDispatcher
from app.system_meter import SystemMeasurement
from .commands import MetricsNotificator


class MetricsLogDispatcher(LogDispatcher[SystemMeasurement], MetricsNotificator):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._events: deque[Event] = deque[Event]()

    def add_notification(self, event: Event):
        self._events.append(event)

    def log(self, data: SystemMeasurement | list[SystemMeasurement]) -> None:
        self._logger.debug("received SystemMeasurement")
        while self._events:
            event = self._events.popleft()
            event.set()
        super().log(data)
