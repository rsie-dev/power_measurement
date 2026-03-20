import logging
from io import BytesIO, TextIOWrapper
from pathlib import Path

from fabric import Connection
import humanize

from experiment.run.log import CountStreamEntry, Logger
from .executor_command import ExecutorCommand, PostChainLink


class CountStreamPostChainLink(PostChainLink):
    def __init__(self, stdout_target: Path | bool, count_logger: Logger[CountStreamEntry]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._stdout_target = stdout_target
        self._count_logger = count_logger
        self._count_output = None

    def name(self) -> str:
        return "count"

    def init(self, nr: int, connection: Connection) -> None:
        result = connection.run("mktemp", hide=True)
        self._count_output = result.stdout.strip()
        self._logger.debug("count output: %s", self._count_output)

    def append(self, command: ExecutorCommand) -> str:
        command_list = [""]
        if isinstance(self._stdout_target, Path):
            command_list.append(f"tee {self._stdout_target}")
        command_list.append(f"wc -c > {self._count_output}")
        post_command = " | ".join(command_list)
        return post_command

    def finish(self, nr: int, command: ExecutorCommand, connection: Connection) -> None:
        if not self._count_output:
            return

        count_buffer = BytesIO()
        connection.get(remote=self._count_output, local=count_buffer)
        entry = self._extract_count(nr, command, count_buffer)
        human_size = humanize.naturalsize(entry.count, binary=True, format="%.3f")
        self._logger.info("Count stdout: %s", human_size)
        self._count_logger.log(entry)
        connection.run(f"rm -f {self._count_output}", hide=True, warn=True)

    def _extract_count(self, nr: int, command: ExecutorCommand, time_file: BytesIO) -> CountStreamEntry:
        time_file.seek(0)
        with TextIOWrapper(time_file, encoding="utf-8") as text_stream:
            line = text_stream.readline()
            count = int(line)
            entry = CountStreamEntry(entry_nr=nr, count=count, command=command.command)
            return entry
