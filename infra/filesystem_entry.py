from dataclasses import dataclass
from pathlib import Path


@dataclass
class FilesystemEntry:
    name: Path
    fs_type: str | None

    def __str__(self):
        return f"FS {self.name} = {self.fs_type}"
