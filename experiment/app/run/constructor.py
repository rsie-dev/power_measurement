from __future__ import annotations
import logging
from typing import List, Optional
from typing import Self

from app.api.api import Builder
from app.api.api import CommandBuilder, HostCommandBuilder, Command, HostBuilder, ExperimentBuilder, RunsBuilder
from app.experiment.steps import Step, InitStep
from app.experiment.steps import SSHHost
from app.experiment.steps import StartSystemMetricsClientStep, TimeDeltaStep
from app.experiment.steps import USBMeterStep, HostCommandStep, CommandExecutor
from app.experiment.steps import HostnameValidationStep, HostnameInfoStep
from app.experiment.experiment_executor import ExperimentExecutor


class Constructor(Builder):
    pass


class CompositeConstructor(Constructor):
    def __init__(self):
        self._steps: List[Step] = []

    def add_steps(self, steps: List[Step]) -> None:
        self._steps.extend(steps)


class CommandConstructor(Constructor, CommandBuilder):
    def __init__(self, parent: HostCommandConstructor, command: str):
        self._parent = parent
        self._command = command
        self._work_dir = None
        self._with_timing = False

    def with_work_dir(self, folder: str) -> Self:
        self._work_dir = folder
        return self

    def with_timing(self) -> Self:
        self._with_timing = True
        return self

    def done(self) -> HostCommandBuilder:
        command = CommandExecutor(self._command, self._with_timing, self._work_dir)
        self._parent.add_command(command)
        return self._parent


class HostCommandConstructor(Constructor, HostCommandBuilder):
    def __init__(self, parent: HostConstructor, host: SSHHost):
        self._parent = parent
        self._host = host
        self._commands: list[Command] = []

    def execute(self, command: str) -> Self:
        self.add_command(CommandExecutor(command))
        return self

    def execute_with(self, command: str) -> CommandBuilder:
        return CommandConstructor(self, command)

    def add_command(self, command: Command) -> None:
        self._commands.append(command)

    def done(self) -> HostBuilder:
        steps = []
        step = HostCommandStep(self._host, self._commands)
        steps.append(step)
        self._parent.add_steps(steps)
        return self._parent


class HostConstructor(CompositeConstructor, HostBuilder):
    def __init__(self, parent: RunsConstructor, host: SSHHost):
        super().__init__()
        self._parent = parent
        self._host = host
        self._serial_number = None

    @property
    def host(self) -> str:
        return self._host.host_name

    def with_usb_meter(self, serial_number: str) -> Self:
        self._serial_number = serial_number
        return self

    def measure_commands(self) -> HostCommandBuilder:
        return HostCommandConstructor(self, self._host)

    def done(self) -> RunsBuilder:
        steps = []
        formatter_class, formatter_config = self._parent.formatter_info
        if self._serial_number:
            formatter = formatter_class(**formatter_config)
            step = USBMeterStep(formatter, self._serial_number)
            steps.append(step)
        if self._parent.collect_metrics:
            formatter = formatter_class(**formatter_config)
            steps.append(TimeDeltaStep(self._host))
            step = StartSystemMetricsClientStep(formatter, self._host)
            steps.append(step)
        steps.extend(self._steps)
        self._parent.add_steps(steps)
        return self._parent


class RunsConstructor(CompositeConstructor, RunsBuilder):
    def __init__(self, parent: ExperimentConstructor):
        super().__init__()
        self._parent = parent
        self._init_steps: List[InitStep] = []

    @property
    def collect_metrics(self) -> bool:
        return self._parent.collect_metrics

    @property
    def formatter_info(self) -> tuple[type, dict]:
        return self._parent.formatter_info

    def on_host(self, host_name: str, host: str, ssh_user: Optional[str] = None) -> HostBuilder:
        ssh_user = ssh_user or "dietpi"
        ssh_host = SSHHost(host_name=host_name, host=host, ssh_user=ssh_user)
        self._init_steps.append(HostnameValidationStep(ssh_host))
        self._init_steps.append(HostnameInfoStep(ssh_host))
        return HostConstructor(self, ssh_host)

    def done(self) -> ExperimentBuilder:
        self._parent.add_init_steps(self._init_steps)
        self._parent.add_steps(self._steps)
        return self._parent


class ExperimentConstructor(CompositeConstructor, ExperimentBuilder):
    def __init__(self, formatter_info: tuple[type, dict]):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._runs: Optional[int] = None
        self._with_metrics_collection: bool = False
        self._init_steps: List[InitStep] = []
        self._formatter_info = formatter_info

    @property
    def collect_metrics(self) -> bool:
        return self._with_metrics_collection

    @property
    def formatter_info(self) -> tuple[type, dict]:
        return self._formatter_info

    def add_init_steps(self, init_steps: List[InitStep]):
        self._init_steps.extend(init_steps)

    def execute_runs(self, runs: int) -> RunsBuilder:
        self._runs = runs
        return RunsConstructor(self)

    def with_metrics_collection(self) -> Self:
        self._with_metrics_collection = True
        return self

    def build(self) -> ExperimentExecutor:
        runs = self._runs or 1
        experiment = ExperimentExecutor(self._init_steps, self._steps, runs, self._with_metrics_collection)
        return experiment
