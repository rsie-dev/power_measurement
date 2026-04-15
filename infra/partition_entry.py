from dataclasses import dataclass
from pathlib import Path


@dataclass
class PartitionEntry:
    node: Path
    start: int
    size: int
    type: str
    bootable: bool

    def __str__(self):
        return f"Partition {self.node}"
