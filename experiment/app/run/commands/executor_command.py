import logging
from typing import Optional

from fabric import Connection

from app.api import Command


class ExecutorCommand(Command):
    def __init__(self, command: str, work_dir: Optional[str] = None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._command: str = command
        self._work_dir = work_dir

    @property
    def command(self):
        return self._command

    @property
    def work_dir(self):
        return self._work_dir

    def execute(self, connection: Connection, resources_path):
        work_dir = self._work_dir if self._work_dir else "."
        self._logger.info("execute: %s", self._command)
        with connection.cd(work_dir):
            connection.run(self._command, hide=True)
