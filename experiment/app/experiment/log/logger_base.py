import logging
import datetime


class LoggerBase:
    def __init__(self, formatter: logging.Formatter):
        self._formatter = formatter

    def _format_time(self, time: datetime.datetime) -> str:
        timestamp = time.timestamp()
        log_record = logging.makeLogRecord({"created": timestamp})
        formatted_time = self._formatter.formatTime(log_record)
        return formatted_time
