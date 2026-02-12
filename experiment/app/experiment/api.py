from __future__ import annotations
import logging
from typing import List, Optional
from typing import Self

from .steps import Step, InitStep
from .steps import StartSystemMetricsClientStep, USBMeterStep, HostCommandStep, Command
from .steps import HostnameValidationStep
from .experiment import Experiment


class Builder:
    pass


class CompositeBuilder(Builder):
    def __init__(self):
        self._steps: List[Step] = []

    def add_steps(self, steps: List[Step]) -> None:
        self._steps.extend(steps)


class CommandBuilder(Builder):
    def __init__(self, parent: HostCommandBuilder, command: str):
        self._parent = parent
        self._command = command
        self._work_dir = None

    def with_work_dir(self, folder: str) -> Self:
        self._work_dir = folder
        return self

    def done(self) -> HostCommandBuilder:
        command = Command(self._command, self._work_dir)
        self._parent.add_command(command)
        return self._parent


class HostCommandBuilder(Builder):
    def __init__(self, parent: HostBuilder, host: str, ssh_user: str):
        self._parent = parent
        self._host = host
        self._ssh_user = ssh_user
        self._commands: list[Command] = []

    def execute(self, command: str) -> Self:
        self.add_command(Command(command))
        return self

    def execute_with(self, command: str) -> CommandBuilder:
        return CommandBuilder(self, command)

    def add_command(self, command: Command) -> None:
        self._commands.append(command)

    def done(self) -> HostBuilder:
        steps = []
        step = HostCommandStep(self._host, self._ssh_user, self._commands)
        steps.append(step)
        self._parent.add_steps(steps)
        return self._parent


class HostBuilder(CompositeBuilder):
    def __init__(self, parent: ExperimentBuilder, host_name: str, host: str, ssh_user: str):
        super().__init__()
        self._parent = parent
        self._host_name = host_name
        self._host = host
        self._ssh_user = ssh_user
        self._serial_number = None

    @property
    def host(self) -> str:
        return self._host_name

    def with_usb_meter(self, serial_number: str) -> Self:
        self._serial_number = serial_number
        return self

    def with_commands(self) -> HostCommandBuilder:
        return HostCommandBuilder(self, self._host, self._ssh_user)

    def done(self) -> ExperimentBuilder:
        steps = []
        if self._serial_number:
            step = USBMeterStep(self._host, self._serial_number)
            steps.append(step)
        if self._parent.collect_metrics:
            step = StartSystemMetricsClientStep(self._host_name, self._host, self._ssh_user)
            steps.append(step)
        steps.extend(self._steps)
        self._parent.add_steps(steps)
        return self._parent


class ExperimentBuilder(CompositeBuilder):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._runs: Optional[int] = None
        self._with_metrics_collection: bool = False
        self._init_steps: List[InitStep] = []

    @property
    def collect_metrics(self) -> bool:
        return self._with_metrics_collection

    def with_runs(self, runs: int) -> Self:
        self._runs = runs
        return self

    def with_metrics_collection(self) -> Self:
        self._with_metrics_collection = True
        return self

    def on_host(self, host_name: str, host: str, ssh_user: Optional[str] = None) -> HostBuilder:
        ssh_user = ssh_user or "dietpi"
        self._init_steps.append(HostnameValidationStep(host_name, host, ssh_user))
        return HostBuilder(self, host_name, host, ssh_user)

    def build(self) -> Experiment:
        runs = self._runs or 1
        experiment = Experiment(self._init_steps, self._steps, runs, self._with_metrics_collection)
        return experiment
