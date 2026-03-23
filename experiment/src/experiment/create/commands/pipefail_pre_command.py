import logging

from fabric import Connection

from .executor_command import ExecutorCommand, PreCommand


class PipefailPreCommand(PreCommand):
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def name(self) -> str:
        return "pipefail"

    def init(self, nr: int, connection: Connection) -> None:
        pass

    def prepend(self, command: ExecutorCommand) -> str:
        pre_command = "set -o pipefail && "
        return pre_command

    def finish(self, nr: int, command: ExecutorCommand, connection: Connection) -> None:
        pass
