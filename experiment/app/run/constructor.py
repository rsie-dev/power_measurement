from __future__ import annotations
import logging
from typing import List, Self

from app.api import Builder
from app.api import HostBuilder, MeasurementExecutionBuilder, WarmupExecutionBuilder, ExperimentBuilder
from app.api import CommandBuilder, MeasuredCommandBuilder, Command
from app.api import ExecutionBuilder
from app.common import SSHHost
from app.experiment.steps import Step, InitStep
from app.experiment.steps import SystemMetricsClientStep, TimeDeltaStep
from app.experiment.steps import WarmupCommandStep, HostCommandStep
from app.experiment.steps import HostnameValidationStep, HostnameInfoStep
from app.experiment.steps import UploadStep, DeleteStep
from app.experiment.steps.measurement import Measurement
from app.experiment.steps.measurement import MultimeterMeasurement
from app.experiment.experiment_executor import ExperimentExecutor
from app.experiment.log import LogProvider, LoggerFactory, GenericLogProvider, LogDispatcher
from app.experiment.log import MetricType, CSVMetricsLogger
from app.experiment.log import CSVMultimeterLogger
from app.experiment.log import FileStatsEntry, CSVFileStatLogger
from app.experiment.log import TimingEntry, CSVTimingLogger
from app.run.commands import ExecutorCommand, DelayCommand, TimedCommand, CompositeCommand, FileStatCommand
from app.usb_meter.measurement import ElectricalMeasurement
from app.system_meter import SystemMeasurement

from .multimeter_device_manager import MultimeterDeviceManager


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
    def __init__(self, parent: HostConstructor, host: SSHHost, runs: int, tag: str):
        super().__init__(host)
        self._parent = parent
        self._runs = runs
        self._tag = tag
        self._serial_number = None
        self._head_delay = None
        self._tail_delay = None
        self._log_dispatcher: dict[object, LogDispatcher] = {}

    def allocate_timing_dispatcher(self) -> LogDispatcher[TimingEntry]:
        if TimingEntry not in self._log_dispatcher:
            self._log_dispatcher[TimingEntry] = LogDispatcher[TimingEntry]()
        return self._log_dispatcher[TimingEntry]

    def allocate_file_stats_dispatcher(self) -> LogDispatcher[FileStatsEntry]:
        if FileStatsEntry not in self._log_dispatcher:
            self._log_dispatcher[FileStatsEntry] = LogDispatcher[FileStatsEntry]()
        return self._log_dispatcher[FileStatsEntry]

    def with_multimeter(self, serial_number: str) -> Self:
        self._serial_number = serial_number
        if ElectricalMeasurement not in self._log_dispatcher:
            self._log_dispatcher[ElectricalMeasurement] = LogDispatcher[ElectricalMeasurement]()
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
        measurements: list[Measurement] = []
        if self._serial_number:
            measurement, multimeter_log_provider = self._create_multimeter()
            log_providers.append(multimeter_log_provider)
            measurements.append(measurement)

        metrics_dispatcher = self._parent.collect_metrics
        if metrics_dispatcher:
            metrics = self._create_metrics(metrics_dispatcher)
            log_providers.extend(metrics[0])
            steps.extend(metrics[1])

        if TimingEntry in self._log_dispatcher:
            log_providers.append(self._create_timing_log_provider())
        if FileStatsEntry in self._log_dispatcher:
            log_providers.append(self._create_file_stats_log_provider())

        commands = self._commands[:]
        if self._head_delay:
            commands.insert(0, DelayCommand(self._head_delay, "head"))
        if self._tail_delay:
            commands.append(DelayCommand(self._tail_delay, "tail"))

        command_config = HostCommandStep.CommandConfig(runs=self._runs, commands=commands, tag=self._tag)
        step = HostCommandStep(self._host, command_config, log_providers, measurements)
        steps.append(step)
        self._parent.add_steps(steps)
        return self._parent

    def _create_metrics(self, metrics_dispatcher: LogDispatcher[SystemMeasurement]) -> (
            tuple)[list[LogProvider], list[Step]]:
        steps: list[Step] = []
        log_providers: list[LogProvider] = []
        formatter_class, formatter_config = self._parent.formatter_info
        formatter = formatter_class(**formatter_config)

        system_log_factory: LoggerFactory = lambda resource_path: CSVMetricsLogger(resource_path / "system.csv",
                                                                                   formatter, MetricType.SYSTEM)
        system_log_provider = GenericLogProvider(metrics_dispatcher, system_log_factory)
        log_providers.append(system_log_provider)

        cpu_log_factory: LoggerFactory = lambda resource_path: CSVMetricsLogger(resource_path / "cpu.csv",
                                                                                formatter, MetricType.CPU)
        cpu_log_provider = GenericLogProvider(metrics_dispatcher, cpu_log_factory)
        log_providers.append(cpu_log_provider)

        return log_providers, steps

    def _create_multimeter(self) -> tuple[Measurement, LogProvider]:
        formatter_class, formatter_config = self._parent.formatter_info
        formatter = formatter_class(**formatter_config)
        multimeter_dispatcher = self._log_dispatcher[ElectricalMeasurement]
        log_factory: LoggerFactory = lambda resource_path: CSVMultimeterLogger(resource_path / "multimeter.csv",
                                                                               formatter)
        multimeter_log_provider = GenericLogProvider(multimeter_dispatcher, log_factory)
        device_manager = MultimeterDeviceManager(self._serial_number)
        device = device_manager.get_device()
        measurement = MultimeterMeasurement(device, multimeter_dispatcher)
        return measurement, multimeter_log_provider

    def _create_timing_log_provider(self) -> LogProvider:
        formatter_class, formatter_config = self._parent.formatter_info
        formatter = formatter_class(**formatter_config)
        log_factory: LoggerFactory = lambda resource_path: CSVTimingLogger(resource_path / "timings.csv", formatter)
        timing_dispatcher = self._log_dispatcher[TimingEntry]
        timing_log_provider = GenericLogProvider(timing_dispatcher, log_factory)
        return timing_log_provider

    def _create_file_stats_log_provider(self) -> LogProvider:
        formatter_class, formatter_config = self._parent.formatter_info
        formatter = formatter_class(**formatter_config)
        log_factory: LoggerFactory = lambda resource_path: CSVFileStatLogger(resource_path / "file_stats.csv",
                                                                             formatter)
        file_stats_dispatcher = self._log_dispatcher[FileStatsEntry]
        file_stats_log_provider = GenericLogProvider(file_stats_dispatcher, log_factory)
        return file_stats_log_provider


class HostConstructor(CompositeConstructor, HostBuilder):
    def __init__(self, parent: ExperimentConstructor, host: SSHHost):
        super().__init__()
        self._parent = parent
        self._host = host
        self._tags: set[str] = set()

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

    def measure_runs(self, runs: int, tag: str = None) -> MeasurementExecutionBuilder:
        if tag is None:
            tag = ""
        if tag in self._tags:
            raise ValueError(f"a measurement with the tag '{tag}' already exists on this host")
        self._tags.add(tag)
        return MeasurementExecutionConstructor(self, self._host, runs, tag)

    def done(self) -> ExperimentBuilder:
        if "" in self._tags and len(self._tags) > 1:
            raise ValueError("each measurement must have an distinctive tag")

        steps = []
        metrics_dispatcher = self._parent.collect_metrics
        if metrics_dispatcher:
            steps.append(TimeDeltaStep(self._host))
            steps.append(SystemMetricsClientStep(self._host, metrics_dispatcher))
        steps.extend(self._steps)
        self._parent.add_steps(steps)
        return self._parent


class ExperimentConstructor(CompositeConstructor, ExperimentBuilder):
    def __init__(self, formatter_info: tuple[type, dict], ssh_user):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._metrics_dispatcher = None
        self._init_steps: List[InitStep] = []
        self._formatter_info = formatter_info
        self._ssh_user = ssh_user

    @property
    def collect_metrics(self) -> LogDispatcher[SystemMeasurement]:
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
        self._metrics_dispatcher = LogDispatcher[SystemMeasurement]()
        return self

    def build(self) -> ExperimentExecutor:
        experiment = ExperimentExecutor(self._init_steps, self._steps, self._metrics_dispatcher)
        return experiment
