from pathlib import Path
from dataclasses import dataclass
import logging
import datetime

from .logger import Logger
from .csv_base_logger import CSVBaseLogger


@dataclass(frozen=True)
class TimingEntry:
    entry_nr: int
    real: datetime.timedelta
    user: datetime.timedelta
    sys: datetime.timedelta
    command: str


class CSVTimingLogger(CSVBaseLogger, Logger[TimingEntry]):
    FIELD_NAMES = ["nr", "real_S", "user_S", "sys_S", "command"]

    def __init__(self, path: Path, formatter: logging.Formatter):
        super().__init__(formatter, path, self.FIELD_NAMES)

    def log(self, data: TimingEntry | list[TimingEntry]) -> None:
        if not isinstance(data, list):
            data = [data]
        for data_entry in data:
            log_entry = {
                "nr": f"{data_entry.entry_nr}",
                "real_S": f"{data_entry.real.total_seconds():8.3f}",
                "user_S": f"{data_entry.user.total_seconds():8.3f}",
                "sys_S": f"{data_entry.sys.total_seconds():8.3f}",
                "command": f"{data_entry.command}",
            }
            self._writer.writerow(log_entry)
