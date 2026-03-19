import logging

from experiment.api import Command


class CompositeCommand(Command):
    def __init__(self, commands: list[Command] = None):
        self._logger = logging.getLogger(self.__class__.__name__)
        if commands is None:
            commands = []
        self._commands = commands

    def execute(self, nr: int, connection, resources_path) -> None:
        for command in self._commands:
            command.execute(nr, connection, resources_path)
