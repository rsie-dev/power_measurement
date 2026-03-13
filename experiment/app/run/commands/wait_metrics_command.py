import logging
from threading import Event

import humanize

from app.api import Command

from .metrics_notificator import MetricsNotificator


class WaitMetricsCommand(Command):
    def __init__(self, metrics_notificator: MetricsNotificator):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._metrics_notificator = metrics_notificator
        self._metrics_client_timeout = 5

    def execute(self, connection, resources_path) -> None:
        self._logger.info("Wait %s for metrics data...", humanize.precisedelta(self._metrics_client_timeout))
        event = Event()
        self._metrics_notificator.add_notification(event)
        event.wait(5)
        self._logger.info("Metrics data arrived")
