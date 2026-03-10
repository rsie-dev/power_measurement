from pathlib import Path
from dataclasses import dataclass
import logging
import datetime

from .logger import Logger
from .csv_base_logger import CSVBaseLogger


@dataclass(frozen=True)
class TimingEntry:
    real: datetime.timedelta
    user: datetime.timedelta
    sys: datetime.timedelta
    command: str


class CSVTimingLogger(CSVBaseLogger, Logger[TimingEntry]):
    FIELD_NAMES = ["entry", "real_S", "user_S", "sys_S", "command"]

    def __init__(self, path: Path, formatter: logging.Formatter):
        super().__init__(formatter, path, self.FIELD_NAMES)
        self._entry = 0

    def log(self, data: TimingEntry | list[TimingEntry]) -> None:
        if not isinstance(data, list):
            data = [data]
        for entry in data:
            self._entry += 1
            log_entry = {
                "entry": f"{self._entry}",
                "real_S": f"{entry.real.total_seconds():8.3f}",
                "user_S": f"{entry.user.total_seconds():8.3f}",
                "sys_S": f"{entry.sys.total_seconds():8.3f}",
                "command": f"{entry.command}",
            }
            self._writer.writerow(log_entry)
