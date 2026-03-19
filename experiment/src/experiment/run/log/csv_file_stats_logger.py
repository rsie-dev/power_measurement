from pathlib import Path
from dataclasses import dataclass
import logging

from .logger import Logger
from .csv_base_logger import CSVBaseLogger


@dataclass(frozen=True)
class FileStatsEntry:
    nr: int
    size: int
    path: str


class CSVFileStatLogger(CSVBaseLogger, Logger[FileStatsEntry]):
    FIELD_NAMES = ["nr", "size", "path"]

    def __init__(self, path: Path, formatter: logging.Formatter):
        super().__init__(formatter, path, self.FIELD_NAMES)

    def log(self, data: FileStatsEntry | list[FileStatsEntry]) -> None:
        if not isinstance(data, list):
            data = [data]
        for entry in data:
            log_entry = {
                "nr": f"{entry.nr}",
                "size": f"{entry.size}",
                "path": f"{entry.path}",
            }
            self._writer.writerow(log_entry)
