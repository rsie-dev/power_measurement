from __future__ import annotations
import logging
from typing import List, Optional
from typing import Self

from .steps import Step, HostStep, HostCommandStep
from .experiment import Experiment


class Builder:
    def build(self):
        pass

    def add_steps(self, steps: List[Step]):
        pass


class HostCommandBuilder(Builder):
    def __init__(self, parent: HostBuilder, host_name: str, ssh_user: str):
        self._parent = parent
        self._host_name = host_name
        self._ssh_user = ssh_user
        self._commands = []

    def execute(self, command) -> Self:
        self._commands.append(command)
        return self

    def done(self) -> HostBuilder:
        step = HostCommandStep(self._host_name, self._ssh_user, self._commands)
        self._parent.add_steps([step])
        return self._parent


class HostBuilder(Builder):
    def __init__(self, parent: ExperimentBuilder, host: str):
        self._parent = parent
        self._host = host
        self._serial_number = None
        self._steps: List[Step] = []

    def with_usb_meter(self, serial_number: str) -> Self:
        self._serial_number = serial_number
        return self

    def execute_commands_on(self, host_name: str, ssh_user: Optional[str] = None) -> HostCommandBuilder:
        ssh_user = ssh_user or "dietpi"
        return HostCommandBuilder(self, host_name, ssh_user)

    def add_steps(self, steps: List[Step]):
        self._steps.extend(steps)

    def done(self) -> ExperimentBuilder:
        steps = []
        if self._serial_number:
            step = HostStep(self._host, self._serial_number)
            steps.append(step)
        steps.extend(self._steps)
        self._parent.add_steps(steps)
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
