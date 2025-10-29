import logging
from typing import List


class Step:
    def __init__(self, name: str):
        self.name = name

    def execute(self):
        pass


class Experiment:
    def __init__(self, steps: List[Step]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._steps = steps

    def _get_steps(self):
        return self._steps[:]

    def run(self):
        """
        Execute the experiment: calls each step.
        """
        for step in self._get_steps():
            self._logger.debug("execute step: %s", step.name)
            step.execute()


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
