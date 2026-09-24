import logging
from io import BytesIO, TextIOWrapper
import datetime

from fabric import Connection
import humanize

from experiment.run.log import DutTimingEntry, Logger
from .executor_command import ExecutorCommand, PreCommand, PostCommand


class DutTimesCommand(PreCommand, PostCommand):
    DATE_COMMAND = "/usr/bin/date"
    DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%3N%:z"

    def __init__(self, timing_logger: Logger[DutTimingEntry]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._timing_logger = timing_logger
        self._timing_output = None

    def name(self) -> str:
        return "dut_times"

    def init(self, nr: int, connection: Connection) -> None:
        if self._timing_output:
            return
        result = connection.run("mktemp", hide=True)
        self._timing_output = result.stdout.strip()
        self._logger.debug("dut timing output: %s", self._timing_output)

    def prepend(self, command: ExecutorCommand) -> str:
        pre_command = f"{self.DATE_COMMAND} '+start: {self.DATE_FORMAT}' > {self._timing_output} && "
        return pre_command

    def append(self, command: ExecutorCommand) -> str:
        post_command = f" && {self.DATE_COMMAND} '+end: {self.DATE_FORMAT}' >> {self._timing_output}"
        return post_command

    def finish(self, nr: int, command: ExecutorCommand, connection: Connection) -> None:
        if not self._timing_output:
            return

        time_buffer = BytesIO()
        try:
            connection.get(remote=self._timing_output, local=time_buffer)
        finally:
            self._timing_output = None

        timing_entry = self._extract_timing_entry(nr, command, time_buffer)
        duration = timing_entry.end - timing_entry.start
        elapsed_str = humanize.precisedelta(duration, minimum_unit="seconds")
        self._logger.info("Execution times: real: %s", elapsed_str)
        self._timing_logger.log(timing_entry)

        connection.run(f"rm -f {self._timing_output}", hide=True, warn=True)

    def _extract_timing_entry(self, nr: int, command: ExecutorCommand, time_file: BytesIO) -> DutTimingEntry:
        entries: dict[str, datetime.datetime] = {}
        time_file.seek(0)
        with TextIOWrapper(time_file, encoding="utf-8") as text_stream:
            for line in text_stream:
                key, value = self._parse_time_line(line)
                entries[key] = value
        return DutTimingEntry(entry_nr=nr,
                              start=entries["start"],
                              end=entries["end"],
                              command=command.command,
                              )

    def _parse_time_line(self, line) -> tuple[str, datetime.datetime]:
        key, _ , timestamp = line.partition(":")
        key = key.strip()
        timestamp = datetime.datetime.fromisoformat(timestamp.strip())
        return key, timestamp
