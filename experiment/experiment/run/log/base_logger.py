from abc import ABC, abstractmethod
import logging
import datetime
from contextlib import contextmanager


class BaseLogger(ABC):
    def __init__(self, formatter: logging.Formatter):
        self._formatter = formatter

    @abstractmethod
    def init(self) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    def _format_time(self, time: datetime.datetime) -> str:
        timestamp = time.timestamp()
        log_record = logging.makeLogRecord({"created": timestamp})
        formatted_time = self._formatter.formatTime(log_record)
        return formatted_time


@contextmanager
def logger(logger_base: BaseLogger):
    logger_base.init()
    try:
        yield logger_base
    finally:
        logger_base.close()
