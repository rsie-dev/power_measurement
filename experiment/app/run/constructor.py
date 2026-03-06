from __future__ import annotations
import logging
from typing import List
from typing import Self

from app.api import Builder
from app.api import HostBuilder, MeasurementExecutionBuilder, WarmupExecutionBuilder, ExperimentBuilder
from app.api import CommandBuilder, MeasuredCommandBuilder, Command
from app.api import ExecutionBuilder
from app.experiment.steps import Step, InitStep
from app.experiment.steps import SSHHost
from app.experiment.steps import SystemMetricsClientStep, TimeDeltaStep
from app.experiment.steps import MultimeterStep, WarmupCommandStep, HostCommandStep
from app.experiment.steps import HostnameValidationStep, HostnameInfoStep
from app.experiment.steps import UploadStep
from app.experiment.steps import LogProvider
from app.experiment.experiment_executor import ExperimentExecutor
from app.run.commands import ExecutorCommand, DelayCommand, TimedCommand

from .timing_dispatcher import TimingDispatcher
from .timing_log_provider import TimingLogProvider


class Constructor(Builder):
    pass


class CompositeConstructor(Constructor):
    def __init__(self):
        super().__init__()
        self._steps: List[Step] = []

    def add_steps(self, steps: List[Step]) -> None:
        self._steps.extend(steps)


class CommandConstructor(Constructor, CommandBuilder):
    def __init__(self, parent: ExecutionConstructor, command: str):
        super().__init__()
        self._parent = parent
        self._command = command
        self._work_dir = None

    def with_work_dir(self, folder: str) -> Self:
        self._work_dir = folder
        return self

    def done(self) -> ExecutionBuilder:
        command = ExecutorCommand(self._command, self._work_dir)
        self._parent.add_command(command)
        return self._parent


class MeasuredCommandConstructor(CommandConstructor, MeasuredCommandBuilder):
    def __init__(self, parent: MeasurementExecutionConstructor, command: str):
        super().__init__(parent, command)
        self._parent = parent
        self._with_timings = False

    def with_timings(self) -> Self:
        self._with_timings = True
        return self

    def done(self) -> ExecutionBuilder:
        command = ExecutorCommand(self._command, self._work_dir)
        if self._with_timings:
            timing_dispatcher = self._parent.allocate_timing_dispatcher()
            command = TimedCommand(command, timing_dispatcher)
        self._parent.add_command(command)
        return self._parent


class ExecutionConstructor(Constructor, ExecutionBuilder):
    def __init__(self, host: SSHHost):
        super().__init__()
        self._host = host
        self._commands: list[Command] = []

    def execute(self, command: str) -> Self:
        self.add_command(ExecutorCommand(command))
        return self

    def execute_with(self, command: str) -> CommandBuilder:
        return CommandConstructor(self, command)

    def add_command(self, command: Command) -> None:
        self._commands.append(command)


class WarmupExecutionConstructor(ExecutionConstructor, WarmupExecutionBuilder):
    def __init__(self, parent: HostConstructor, host: SSHHost):
        super().__init__(host)
        self._parent = parent

    def done(self) -> HostBuilder:
        steps = []
        commands = self._commands[:]
        step = WarmupCommandStep(self._host, commands)
        steps.append(step)
        self._parent.add_steps(steps)
        return self._parent


class MeasurementExecutionConstructor(ExecutionConstructor, MeasurementExecutionBuilder):
    def __init__(self, parent: HostConstructor, host: SSHHost, runs: int):
        super().__init__(host)
        self._parent = parent
        self._runs = runs
        self._serial_number = None
        self._head_delay = None
        self._tail_delay = None
        self._timing_dispatcher = None

    def allocate_timing_dispatcher(self) -> TimingDispatcher:
        if not self._timing_dispatcher:
            self._timing_dispatcher = TimingDispatcher()
        return self._timing_dispatcher

    def with_multimeter(self, serial_number: str) -> Self:
        self._serial_number = serial_number
        return self

    def with_head_delay(self, delay: int) -> Self:
        self._head_delay = delay
        return self

    def with_tail_delay(self, delay: int) -> Self:
        self._tail_delay = delay
        return self

    def execute_with(self, command: str) -> MeasuredCommandBuilder:
        return MeasuredCommandConstructor(self, command)

    def done(self) -> HostBuilder:
        steps = []

        log_providers: list[LogProvider] = []
        formatter_class, formatter_config = self._parent.formatter_info
        if self._serial_number:
            formatter = formatter_class(**formatter_config)
            step = MultimeterStep(formatter, self._serial_number)
            log_providers.append(step)
            steps.append(step)
        if self._parent.collect_metrics:
            formatter = formatter_class(**formatter_config)
            steps.append(TimeDeltaStep(self._host))
            step = SystemMetricsClientStep(formatter, self._host)
            log_providers.append(step)
            steps.append(step)

        if self._timing_dispatcher:
            formatter = formatter_class(**formatter_config)
            timing_log_provider = TimingLogProvider(self._timing_dispatcher, formatter)
            log_providers.append(timing_log_provider)

            #commands = []
            #for command in self._commands:
            #    if isinstance(command, ExecutorCommand):
            #        commands.append(TimedCommand(command, timing_dispatcher))
            #    else:
            #        commands.append(command)
        else:
            #commands = self._commands[:]
            pass

        commands = self._commands[:]
        if self._head_delay:
            commands.insert(0, DelayCommand(self._head_delay, "head"))
        if self._tail_delay:
            commands.append(DelayCommand(self._tail_delay, "tail"))

        step = HostCommandStep(self._host, commands, self._runs, log_providers)
        steps.append(step)
        self._parent.add_steps(steps)
        return self._parent


class HostConstructor(CompositeConstructor, HostBuilder):
    def __init__(self, parent: ExperimentConstructor, host: SSHHost):
        super().__init__()
        self._parent = parent
        self._host = host

    @property
    def collect_metrics(self) -> bool:
        return self._parent.collect_metrics

    @property
    def formatter_info(self) -> tuple[type, dict]:
        return self._parent.formatter_info

    def upload(self, local: str, remote: str) -> Self:
        self._steps.append(UploadStep(self._host, local, remote))
        return self

    def with_warmup(self) -> WarmupExecutionBuilder:
        return WarmupExecutionConstructor(self, self._host)

    def measure_runs(self, runs: int) -> MeasurementExecutionBuilder:
        return MeasurementExecutionConstructor(self, self._host, runs)

    def done(self) -> ExperimentBuilder:
        self._parent.add_steps(self._steps)
        return self._parent


class ExperimentConstructor(CompositeConstructor, ExperimentBuilder):
    def __init__(self, formatter_info: tuple[type, dict], ssh_user):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._with_metrics_collection: bool = False
        self._init_steps: List[InitStep] = []
        self._formatter_info = formatter_info
        self._ssh_user = ssh_user

    @property
    def collect_metrics(self) -> bool:
        return self._with_metrics_collection

    @property
    def formatter_info(self) -> tuple[type, dict]:
        return self._formatter_info

    def add_init_steps(self, init_steps: List[InitStep]):
        self._init_steps.extend(init_steps)

    def on_host(self, host_name: str, host: str) -> HostBuilder:
        ssh_host = SSHHost(host_name=host_name, host=host, ssh_user=self._ssh_user)
        self._init_steps.append(HostnameValidationStep(ssh_host))
        self._init_steps.append(HostnameInfoStep(ssh_host))
        return HostConstructor(self, ssh_host)

    def with_metrics_collection(self) -> Self:
        self._with_metrics_collection = True
        return self

    def build(self) -> ExperimentExecutor:
        experiment = ExperimentExecutor(self._init_steps, self._steps, self._with_metrics_collection)
        return experiment
