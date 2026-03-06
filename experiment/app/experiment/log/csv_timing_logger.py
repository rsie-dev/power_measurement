from pathlib import Path
from dataclasses import dataclass
import csv
import logging
from abc import ABC, abstractmethod
import datetime

from .logger_base import LoggerBase


@dataclass(frozen=True)
class TimingEntry:
    real: datetime.timedelta
    user: datetime.timedelta
    sys: datetime.timedelta
    command: str


class TimingLogger(ABC):
    @abstractmethod
    def log(self, data: TimingEntry) -> None:
        pass


class CSVTimingLogger(LoggerBase, TimingLogger):
    FIELD_NAMES = ["entry", "real_S", "user_S", "sys_S", "command"]

    def __init__(self, path: Path, formatter: logging.Formatter):
        super().__init__(formatter)
        self._stream = path.open(mode="w", encoding="utf-8")
        self._writer = csv.DictWriter(self._stream, fieldnames=self.FIELD_NAMES)
        self._entry = 0

    def init(self) -> None:
        self._writer.writeheader()

    def close(self) -> None:
        self._stream.close()

    def log(self, data: TimingEntry) -> None:
        self._entry += 1
        entry = {
            "entry": f"{self._entry}",
            "real_S": f"{data.real.total_seconds():8.3f}",
            "user_S": f"{data.user.total_seconds():8.3f}",
            "sys_S": f"{data.sys.total_seconds():8.3f}",
            "command": f"{data.command}",
        }
        self._writer.writerow(entry)
