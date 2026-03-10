from pathlib import Path
from dataclasses import dataclass
import logging

from .logger import Logger
from .csv_base_logger import CSVBaseLogger


@dataclass(frozen=True)
class FileStatsEntry:
    size: int
    path: str


class CSVFileStatLogger(CSVBaseLogger, Logger[FileStatsEntry]):
    FIELD_NAMES = ["entry", "size", "path"]

    def __init__(self, path: Path, formatter: logging.Formatter):
        super().__init__(formatter, path, self.FIELD_NAMES)
        self._entry = 0

    def log(self, data: FileStatsEntry) -> None:
        self._entry += 1
        log_entry = {
            "entry": f"{self._entry}",
            "size": f"{data.size}",
            "path": f"{data.path}",
        }
        self._writer.writerow(log_entry)
