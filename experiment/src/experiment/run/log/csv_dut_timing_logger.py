from pathlib import Path
from dataclasses import dataclass
import logging
import datetime

from .logger import Logger
from .csv_base_logger import CSVBaseLogger


@dataclass(frozen=True)
class DutTimingEntry:
    entry_nr: int
    start: datetime.datetime
    end: datetime.datetime
    command: str


class CSVDutTimingLogger(CSVBaseLogger, Logger[DutTimingEntry]):
    FIELD_NAMES = ["nr", "start", "end", "command"]

    def __init__(self, path: Path, formatter: logging.Formatter):
        super().__init__(formatter, path, self.FIELD_NAMES)

    def init(self) -> None:
        super().init()
        entry = {
            "nr": "No Unit",
            "start": "No Unit",
            "end": "No Unit",
            "command": "No Unit",
        }
        self._writer.writerow(entry)

    def log(self, data: DutTimingEntry | list[DutTimingEntry]) -> None:
        if not isinstance(data, list):
            data = [data]
        for data_entry in data:
            log_entry = {
                "nr": f"{data_entry.entry_nr}",
                "start": self._format_time(data_entry.start),
                "end": self._format_time(data_entry.end),
                "command": f"{data_entry.command}",
            }
            self._writer.writerow(log_entry)
