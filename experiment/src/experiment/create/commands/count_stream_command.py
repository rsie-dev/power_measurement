import logging
from io import BytesIO, TextIOWrapper
from pathlib import Path

from fabric import Connection

from experiment.api import Command
from experiment.run.log import CountStreamEntry, Logger
from .executor_command import ExecutorCommand


class CountStreamCommand(Command):
    def __init__(self, command: ExecutorCommand, stdout_target: None | Path, count_logger: Logger[CountStreamEntry]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._command = command
        self._stdout_target = stdout_target
        self._count_logger = count_logger

    def execute(self, nr: int, connection: Connection, resources_path):
        exec_info = " count"
        result = connection.run("mktemp", hide=True)
        count_output = result.stdout.strip()
        self._logger.debug("count output: %s", count_output)

        command = f"{self._command.command} | tee {self._stdout_target} | wc -c > {count_output}"

        work_dir = self._command.work_dir if self._command.work_dir else "."
        self._logger.info("Execute[%02d,%s]: %s", nr, exec_info, self._command.command)
        with ((connection.cd(work_dir))):
            self._logger.info("remote execute: %s", command)
            connection.run(command, hide=True)
            count_buffer = BytesIO()
            connection.get(remote=count_output, local=count_buffer)
            entry = self._extract_count(nr, count_buffer)
            self._logger.warning("read count: %s", entry.count)
            self._count_logger.log(entry)
        connection.run(f"rm -f {count_output}", hide=True, warn=True)

    def _extract_count(self, nr: int, time_file: BytesIO) -> CountStreamEntry:
        time_file.seek(0)
        with TextIOWrapper(time_file, encoding="utf-8") as text_stream:
            line = text_stream.readline()
            count = int(line)
            entry = CountStreamEntry(entry_nr=nr, count=count, command=self._command.command)
            return entry
