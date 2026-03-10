from pathlib import Path
from dataclasses import dataclass
import csv
import logging
from abc import ABC, abstractmethod

from .logger_base import LoggerBase


@dataclass(frozen=True)
class FileStatsEntry:
    size: int
    path: str


class FileStatsLogger(ABC):
    @abstractmethod
    def log(self, data: FileStatsEntry) -> None:
        pass


class CSVFileStatLogger(LoggerBase, FileStatsLogger):
    FIELD_NAMES = ["entry", "size", "path"]

    def __init__(self, path: Path, formatter: logging.Formatter):
        super().__init__(formatter)
        self._stream = path.open(mode="w", encoding="utf-8")
        self._writer = csv.DictWriter(self._stream, fieldnames=self.FIELD_NAMES)
        self._entry = 0

    def init(self) -> None:
        self._writer.writeheader()

    def close(self) -> None:
        self._stream.close()

    def log(self, data: FileStatsEntry) -> None:
        self._entry += 1
        entry = {
            "entry": f"{self._entry}",
            "size": f"{data.size}",
            "path": f"{data.path}",
        }
        self._writer.writerow(entry)
