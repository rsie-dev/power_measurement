from __future__ import annotations
import logging
from typing import List, Self

from app.api import Builder
from app.api import HostBuilder, MeasurementExecutionBuilder, WarmupExecutionBuilder, ExperimentBuilder
from app.api import CommandBuilder, MeasuredCommandBuilder, Command
from app.api import ExecutionBuilder
from app.experiment.steps import Step, InitStep
from app.experiment.steps import SSHHost
from app.experiment.steps import SystemMetricsClientStep, TimeDeltaStep
from app.experiment.steps import MultimeterStep, WarmupCommandStep, HostCommandStep
from app.experiment.steps import HostnameValidationStep, HostnameInfoStep
from app.experiment.steps import UploadStep, DeleteStep
from app.experiment.steps import LogProvider, LoggerFactory, GenericLogProvider
from app.experiment.experiment_executor import ExperimentExecutor
from app.experiment.log import LogDispatcher
from app.experiment.log import MetricType, CSVMetricsLogger
from app.experiment.log import CSVMultimeterLogger
from app.experiment.log import FileStatsEntry, CSVFileStatLogger
from app.experiment.log import TimingEntry, CSVTimingLogger
from app.run.commands import ExecutorCommand, DelayCommand, TimedCommand, CompositeCommand, FileStatCommand
from app.usb_meter.measurement import ElectricalMeasurement
from app.system_meter import SystemMeasurement


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
        self._file_stats: set[str] = set()

    def with_timings(self) -> Self:
        self._with_timings = True
        return self

    def collect_file_stats(self, path: str) -> Self:
        self._file_stats.add(path)
        return self

    def done(self) -> ExecutionBuilder:
        command = ExecutorCommand(self._command, self._work_dir)
        if self._with_timings:
            timing_dispatcher = self._parent.allocate_timing_dispatcher()
            command = TimedCommand(command, timing_dispatcher)
        if self._file_stats:
            commands = [command]
            file_stats_dispatcher = self._parent.allocate_file_stats_dispatcher()
            for path in self._file_stats:
                commands.append(FileStatCommand(path, file_stats_dispatcher))
            command = CompositeCommand(commands)
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
        self._file_stats_dispatcher = None
        self._multimeter_dispatcher = None

    def allocate_timing_dispatcher(self) -> LogDispatcher[TimingEntry]:
        if not self._timing_dispatcher:
            self._timing_dispatcher = LogDispatcher[TimingEntry]()
        return self._timing_dispatcher

    def allocate_file_stats_dispatcher(self) -> LogDispatcher[FileStatsEntry]:
        if not self._file_stats_dispatcher:
            self._file_stats_dispatcher = LogDispatcher[FileStatsEntry]()
        return self._file_stats_dispatcher

    def with_multimeter(self, serial_number: str) -> Self:
        self._serial_number = serial_number
        if self._multimeter_dispatcher is None:
            self._multimeter_dispatcher = LogDispatcher[ElectricalMeasurement]()
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
            log_factory: LoggerFactory = lambda resource_path: CSVMultimeterLogger(resource_path / "multimeter.csv",
                                                                                   formatter)
            multimeter_log_provider = GenericLogProvider(self._multimeter_dispatcher, log_factory)
            step = MultimeterStep(self._serial_number, self._multimeter_dispatcher)
            log_providers.append(multimeter_log_provider)
            steps.append(step)

        metrics_dispatcher = self._parent.collect_metrics
        if metrics_dispatcher:
            formatter = formatter_class(**formatter_config)
            steps.append(TimeDeltaStep(self._host))
            step = SystemMetricsClientStep(self._host, metrics_dispatcher)
            system_log_factory: LoggerFactory = lambda resource_path: CSVMetricsLogger(resource_path / "system.csv",
                                                                                       formatter, MetricType.SYSTEM)
            system_log_provider = GenericLogProvider(metrics_dispatcher, system_log_factory)
            log_providers.append(system_log_provider)
            cpu_log_factory: LoggerFactory = lambda resource_path: CSVMetricsLogger(resource_path / "cpu.csv",
                                                                                    formatter, MetricType.CPU)
            cpu_log_provider = GenericLogProvider(metrics_dispatcher, cpu_log_factory)
            log_providers.append(cpu_log_provider)
            steps.append(step)

        if self._timing_dispatcher:
            log_providers.append(self._create_timing_log_provider())
        if self._file_stats_dispatcher:
            log_providers.append(self._create_file_stats_log_provider())

        commands = self._commands[:]
        if self._head_delay:
            commands.insert(0, DelayCommand(self._head_delay, "head"))
        if self._tail_delay:
            commands.append(DelayCommand(self._tail_delay, "tail"))

        step = HostCommandStep(self._host, commands, self._runs, log_providers)
        steps.append(step)
        self._parent.add_steps(steps)
        return self._parent

    def _create_timing_log_provider(self) -> LogProvider:
        formatter_class, formatter_config = self._parent.formatter_info
        formatter = formatter_class(**formatter_config)
        log_factory: LoggerFactory = lambda resource_path: CSVTimingLogger(resource_path / "timings.csv", formatter)
        timing_log_provider = GenericLogProvider(self._timing_dispatcher, log_factory)
        return timing_log_provider

    def _create_file_stats_log_provider(self) -> LogProvider:
        formatter_class, formatter_config = self._parent.formatter_info
        formatter = formatter_class(**formatter_config)
        log_factory: LoggerFactory = lambda resource_path: CSVFileStatLogger(resource_path / "file_stats.csv",
                                                                             formatter)
        file_stats_log_provider = GenericLogProvider(self._file_stats_dispatcher, log_factory)
        return file_stats_log_provider


class HostConstructor(CompositeConstructor, HostBuilder):
    def __init__(self, parent: ExperimentConstructor, host: SSHHost):
        super().__init__()
        self._parent = parent
        self._host = host

    @property
    def collect_metrics(self) -> LogDispatcher[SystemMeasurement]:
        return self._parent.collect_metrics

    @property
    def formatter_info(self) -> tuple[type, dict]:
        return self._parent.formatter_info

    def upload(self, local: str, remote: str) -> Self:
        self._steps.append(UploadStep(self._host, local, remote))
        return self

    def delete(self, remote: str) -> Self:
        self._steps.append(DeleteStep(self._host, remote))
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
        #self._with_metrics_collection: bool = False
        self._metrics_dispatcher = None
        self._init_steps: List[InitStep] = []
        self._formatter_info = formatter_info
        self._ssh_user = ssh_user

    @property
    def collect_metrics(self) -> LogDispatcher[SystemMeasurement]:
        #return self._with_metrics_collection
        return self._metrics_dispatcher

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
        #self._with_metrics_collection = True
        self._metrics_dispatcher = LogDispatcher[SystemMeasurement]()
        return self

    def build(self) -> ExperimentExecutor:
        experiment = ExperimentExecutor(self._init_steps, self._steps, self._metrics_dispatcher)
        return experiment
