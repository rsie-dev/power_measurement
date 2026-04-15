from dataclasses import dataclass
from pathlib import Path


@dataclass
class PartitionEntry:
    node: Path
    start: int
    size: int
    type: str
    bootable: bool
