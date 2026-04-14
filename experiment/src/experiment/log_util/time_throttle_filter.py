import logging
from datetime import datetime, timedelta


class TimeThrottleFilter(logging.Filter):
    def __init__(self, interval: timedelta):
        super().__init__()
        self._interval = interval
        self._last_log_time = datetime.now()

    def filter(self, record):
        now = datetime.now()
        if now - self._last_log_time >= self._interval:
            self._last_log_time = now
            return True
        return False
