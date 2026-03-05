import logging
from io import BytesIO, TextIOWrapper

from fabric import Connection

from app.api import Command
from app.experiment.log import TimingEntry, TimingLogger
from .executor_command import ExecutorCommand

class TimedCommand(Command):
    def __init__(self, timed_command: ExecutorCommand, timing_logger: TimingLogger):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._timed_command = timed_command
        self._timing_logger = timing_logger

    def execute(self, connection: Connection, resources_path):
        exec_info = " [timed]"
        result = connection.run("mktemp", hide=True)
        timing_output = result.stdout.strip()
        self._logger.debug("timing output: %s", timing_output)
        command = f"/usr/bin/time -p -o {timing_output} {self._timed_command.command}"
        work_dir = self._timed_command.work_dir if self._timed_command.work_dir else "."
        self._logger.info("execute%s: %s", exec_info, self._timed_command.command)
        with connection.cd(work_dir):
            connection.run(command, hide=True)
            time_info = BytesIO()
            connection.get(remote=timing_output, local=time_info)
            timing_entry = self._extract_timing_entry(time_info)
            timings = f"real: {timing_entry.real:.2f} user: {timing_entry.user:.2f} sys: {timing_entry.sys:.2f}"
            self._logger.info("execution times: %s", timings)
            self._timing_logger.log(timing_entry)

    def _extract_timing_entry(self, time_file: BytesIO) -> TimingEntry:
        entries = {}
        time_file.seek(0)
        with TextIOWrapper(time_file, encoding="utf-8") as text_stream:
            for line in text_stream:
                key, value = line.strip().split(maxsplit=1)
                entries[key] = float(value)
        return TimingEntry(entries["real"], entries["user"], entries["sys"], self._timed_command.command)
