from __future__ import annotations
import logging
from typing import Optional
from abc import ABC, abstractmethod

from fabric import Connection

from experiment.api import Command


class CommandExtender(ABC):
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def init(self, nr: int, connection: Connection) -> None:
        pass

    @abstractmethod
    def finish(self, nr: int, command: ExecutorCommand, connection: Connection) -> None:
        pass


class PreCommand(CommandExtender):
    @abstractmethod
    def prepend(self, command: ExecutorCommand) -> str:
        pass


class PostCommand(CommandExtender):
    @abstractmethod
    def append(self, command: ExecutorCommand) -> str:
        pass


class ExecutorCommand(Command):
    def __init__(self, command: str, work_dir: Optional[str] = None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._command: str = command
        self._work_dir = work_dir
        self._prepend_chain: list[PreCommand] = []
        self._append_chain: list[PostCommand] = []

    def prepend(self, link: PreCommand) -> None:
        self._prepend_chain.append(link)

    def append(self, link: PostCommand) -> None:
        self._append_chain.append(link)

    @property
    def command(self):
        return self._command

    @property
    def work_dir(self):
        return self._work_dir

    def execute(self, nr: int, connection: Connection, resources_path):
        links = self._prepend_chain + self._append_chain
        tags = ["%02d" % nr]
        tags.extend([link.name() for link in links])

        work_dir = self._work_dir if self._work_dir else "."
        self._logger.info("Execute[%s]: %s", ",".join(tags), self._command)
        with connection.cd(work_dir):
            for link in links:
                link.init(nr, connection)

            command = self._command
            for link in self._prepend_chain:
                prepend = link.prepend(self)
                command = prepend + command
            for link in self._append_chain:
                append = link.append(self)
                command = command + append

            self._logger.debug("remote execute: %s", command)
            result = connection.run(command, hide=True)
            self._logger.debug("command returned with exit code: %d", result.return_code)

            for link in links:
                link.finish(nr, self, connection)
