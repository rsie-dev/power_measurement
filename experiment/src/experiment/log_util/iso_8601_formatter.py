import logging
from datetime import datetime, timezone


class ISO8601Formatter(logging.Formatter):
    def formatTime(self, record, datefmt=None) -> str:
        # record.created is seconds since epoch (float)
        ts = record.created
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        # convert to local timezone
        dt = dt.astimezone()
        return dt.isoformat(timespec="milliseconds")
