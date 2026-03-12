import logging
from pathlib import Path
import csv

from .base_logger import BaseLogger


class CSVBaseLogger(BaseLogger):
    def __init__(self, formatter: logging.Formatter, path: Path, field_names: list[str]):
        super().__init__(formatter)
        self._stream = path.open(mode="x", encoding="utf-8")
        self._writer = csv.DictWriter(self._stream, fieldnames=field_names)

    def init(self) -> None:
        self._writer.writeheader()

    def close(self) -> None:
        self._stream.close()
