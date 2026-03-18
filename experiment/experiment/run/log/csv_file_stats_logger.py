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
        self._index = 0

    def log(self, data: FileStatsEntry | list[FileStatsEntry]) -> None:
        if not isinstance(data, list):
            data = [data]
        for entry in data:
            self._index += 1
            log_entry = {
                "entry": f"{self._index}",
                "size": f"{entry.size}",
                "path": f"{entry.path}",
            }
            self._writer.writerow(log_entry)
