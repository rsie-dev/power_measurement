import logging

from app.api import Command
from app.experiment.log import FileStatsEntry, Logger


class FileStatCommand(Command):
    def __init__(self, path: str, logger: Logger[FileStatsEntry]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._path = path
        self._logger = logger

    def execute(self, connection, resources_path) -> None:
        command = f"stat -c %s {self._path}"
        result = connection.run(command, hide=True)
        remote_size = int(result.stdout.strip())
        entry = FileStatsEntry(path=self._path, size=remote_size)
        self._logger.log(entry)
