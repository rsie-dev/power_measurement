import logging
from typing import List

from .experiment import Experiment, Step


class Builder:
    def build(self):
        pass

    def add_steps(self, steps: List[Step]):
        pass


class HostStep(Step):
    def __init__(self, host: str, commands):
        super().__init__("host")
        self._host = host
        self._commands = commands

    def execute(self):
        print("on host: %s execute: %s" % (self._host, ",".join(self._commands)))


class HostBuilder(Builder):
    def __init__(self, parent: Builder, host):
        self._parent = parent
        self._host = host
        self._commands = []

    def execute(self, command) -> Builder:
        self._commands.append(command)
        return self

    def build(self) -> Builder:
        step = HostStep(self._host, self._commands)
        self._parent.add_steps([step])
        return self._parent


class ExperimentBuilder(Builder):
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._steps: List[Step] = []

    def add_steps(self, steps: List[Step]):
        self._steps.extend(steps)

    def on_host(self, host: str) -> HostBuilder:
        return HostBuilder(self, host)

    def build(self) -> Experiment:
        experiment = Experiment(self._steps)
        return experiment
