from abc import ABC, abstractmethod
from threading import Event


class MetricsNotificator(ABC):
    @abstractmethod
    def add_notification(self, event: Event) -> None:
        pass
