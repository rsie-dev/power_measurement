from pathlib import Path
from dataclasses import dataclass
import logging

from .logger import Logger
from .csv_base_logger import CSVBaseLogger


@dataclass(frozen=True)
class CountStreamEntry:
    entry_nr: int
    count: int
    command: str


class CSVCountStreamLogger(CSVBaseLogger, Logger[CountStreamEntry]):
    FIELD_NAMES = ["nr", "count_B", "command"]

    def __init__(self, path: Path, formatter: logging.Formatter):
        super().__init__(formatter, path, self.FIELD_NAMES)

    def log(self, data: CountStreamEntry | list[CountStreamEntry]) -> None:
        if not isinstance(data, list):
            data = [data]
        for data_entry in data:
            log_entry = {
                "nr": f"{data_entry.entry_nr}",
                "count_B": f"{data_entry.count}",
                "command": f"{data_entry.command}",
            }
            self._writer.writerow(log_entry)
