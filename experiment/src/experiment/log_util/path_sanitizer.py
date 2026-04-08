import logging
from pathlib import Path
import re


class PathSanitizer(logging.Filter):
    def __init__(self):
        super().__init__()
        self._wd = Path.cwd()

    def filter(self, record):
        if record.name == "fabric":
            if record.msg.startswith("Massaged relative local path"):
                record.msg = re.sub(r"into '/[^ ]+", "into [REDACTED_PATH]", str(record.msg))
                return record
            if record.msg.startswith("Uploading"):
                record.msg = re.sub(r"Uploading '/[^ ]+", "Uploading [REDACTED_PATH]", str(record.msg))
                return record
        return True
