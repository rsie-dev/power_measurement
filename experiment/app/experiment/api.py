from __future__ import annotations
import logging
from typing import List, Optional
from typing import Self

from .steps import Step, HostStep
from .experiment import Experiment


class Builder:
    def build(self):
        pass

    def add_steps(self, steps: List[Step]):
        pass


class HostBuilder(Builder):
    def __init__(self, parent: ExperimentBuilder, host: str, host_name: str, ssh_user: str):
        self._parent = parent
        self._host = host
        self._host_name = host_name
        self._ssh_user = ssh_user
        self._commands = []

    def execute(self, command) -> Self:
        self._commands.append(command)
        return self

    def done(self) -> ExperimentBuilder:
        step = HostStep(self._host, self._host_name, self._ssh_user, self._commands)
        self._parent.add_steps([step])
        return self._parent


class ExperimentBuilder(Builder):
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._steps: List[Step] = []

    def add_steps(self, steps: List[Step]):
        self._steps.extend(steps)

    def on_host(self, host: str, host_name: Optional[str] = None, ssh_user: Optional[str] = None) -> HostBuilder:
        node_name = host_name or host
        ssh_user = ssh_user or "dietpi"
        return HostBuilder(self, host, node_name, ssh_user)

    def build(self) -> Experiment:
        experiment = Experiment(self._steps)
        return experiment
