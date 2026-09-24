import logging

from fabric import Connection

from .executor_command import ExecutorCommand, PostCommand


class DevNullPostCommand(PostCommand):
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)

    def name(self) -> str:
        return "to /dev/null"

    def init(self, nr: int, connection: Connection) -> None:
        pass

    def append(self, command: ExecutorCommand) -> str:
        post_command = " > /dev/null"
        return post_command

    def finish(self, nr: int, command: ExecutorCommand, connection: Connection) -> None:
        pass
