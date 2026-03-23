from pathlib import Path
from dataclasses import dataclass
import logging
from enum import Enum, auto
import datetime

from .logger import Logger
from .csv_base_logger import CSVBaseLogger


class MarkerKind(Enum):
    START = auto()
    END = auto()


@dataclass(frozen=True)
class MarkersEntry:
    entry_nr: int
    kind: MarkerKind
    timestamp: datetime.datetime
    command: str


class CSVMarkersLogger(CSVBaseLogger, Logger[MarkersEntry]):
    FIELD_NAMES = ["nr", "kind", "timestamp", "command"]

    def __init__(self, path: Path, formatter: logging.Formatter):
        super().__init__(formatter, path, self.FIELD_NAMES)

    def log(self, data: MarkersEntry | list[MarkersEntry]) -> None:
        if not isinstance(data, list):
            data = [data]
        for data_entry in data:
            formatted_time = self._format_time(data_entry.timestamp)
            marker_entry = {
                "nr": f"{data_entry.entry_nr}",
                "kind": f"{data_entry.kind.name}",
                "timestamp": f"{formatted_time}",
                "command": f"{data_entry.command}",
            }
            self._writer.writerow(marker_entry)
