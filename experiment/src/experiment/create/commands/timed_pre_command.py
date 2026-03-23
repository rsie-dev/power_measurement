import logging
from io import BytesIO, TextIOWrapper
import datetime

from fabric import Connection

from experiment.run.log import TimingEntry, Logger
from .executor_command import ExecutorCommand, PreCommand


def _parse_time_line(line) -> tuple[str, datetime.timedelta]:
    key, value = line.strip().split(maxsplit=1)
    return key, datetime.timedelta(seconds=float(value))


class TimedCommandPreCommand(PreCommand):
    def __init__(self, timing_logger: Logger[TimingEntry]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._count_logger = timing_logger
        self._timing_logger = timing_logger
        self._timing_output = None
        self._threshold = datetime.timedelta(milliseconds=100)

    def name(self) -> str:
        return "timed"

    def init(self, nr: int, connection: Connection) -> None:
        result = connection.run("mktemp", hide=True)
        self._timing_output = result.stdout.strip()
        self._logger.debug("timing output: %s", self._timing_output)

    def prepend(self, command: ExecutorCommand) -> str:
        pre_command = f"/usr/bin/time -p -o {self._timing_output} "
        return pre_command

    def finish(self, nr: int, command: ExecutorCommand, connection: Connection) -> None:
        if not self._timing_output:
            return

        time_buffer = BytesIO()
        connection.get(remote=self._timing_output, local=time_buffer)
        timing_entry = self._extract_timing_entry(nr, command, time_buffer)
        timings = (
            f"real: {timing_entry.real.total_seconds():.2f} "
            f"user: {timing_entry.user.total_seconds():.2f} "
            f"sys: {timing_entry.sys.total_seconds():.2f} "
        )
        extra = self._analysze_timings(timing_entry)
        self._logger.info("Execution times:\t%s%s", timings, extra)
        self._timing_logger.log(timing_entry)

        connection.run(f"rm -f {self._timing_output}", hide=True, warn=True)

    def _extract_timing_entry(self, nr: int, command: ExecutorCommand, time_file: BytesIO) -> TimingEntry:
        entries: dict[str, datetime.timedelta] = {}
        time_file.seek(0)
        with TextIOWrapper(time_file, encoding="utf-8") as text_stream:
            for line in text_stream:
                key, value = _parse_time_line(line)
                entries[key] = value
        return TimingEntry(entry_nr=nr,
                           real=entries["real"],
                           user=entries["user"],
                           sys=entries["sys"],
                           command=command.command)

    def _analysze_timings(self, timing_entry):
        result = []
        # multithread (user + sys >> real) and I/O bound (user + sys << real)
        process_time = timing_entry.user + timing_entry.sys - timing_entry.real
        if timing_entry.user + timing_entry.sys > timing_entry.real:
            if process_time > self._threshold:
                result.append("multithreaded")
        wait_time = timing_entry.real - timing_entry.user - timing_entry.sys
        if timing_entry.user + timing_entry.sys < timing_entry.real:
            if wait_time > self._threshold:
                result.append("I/O bound")

        if not result:
            return ""
        return " [%s]" % ", ".join(result)
