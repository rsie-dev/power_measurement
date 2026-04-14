from __future__ import annotations

from datetime import timedelta
import logging
from typing import List, Self
from dataclasses import dataclass, field
from pathlib import Path

from usb_multimeter import ElectricalMeasurement

from experiment.api import Builder
from experiment.api import HostBuilder, MeasurementExecutionBuilder, WarmupExecutionBuilder, ExperimentBuilder
from experiment.api import CommandBuilder, MeasuredCommandBuilder, Command
from experiment.api import InitializationBuilder, ShutdownBuilder
from experiment.api import ExecutionBuilder
from experiment.common import SSHHost
from experiment.ssh import ConnectionFactory
from experiment.run.steps import Step, InitStep
from experiment.run.steps import SystemMetricsClientStep, TimeDeltaStep
from experiment.run.steps import WarmupCommandStep, MeasurementStep
from experiment.run.steps import HostnameValidationStep, HostnameInfoStep
from experiment.run.steps import UploadStep, DownloadStep, DeleteStep
from experiment.run.steps import TempMonitorStep
from experiment.run.steps.measurement import MultimeterMeasurement
from experiment.run.experiment_executor import ExperimentExecutor
from experiment.run.log import LogProvider, LoggerFactory, GenericLogProvider, LogDispatcher
from experiment.run.log import MetricType, CSVMetricsLogger
from experiment.run.log import CSVMultimeterLogger, CSVTemperatureLogger
from experiment.run.log import FileStatsEntry, CSVFileStatLogger
from experiment.run.log import TimingEntry, CSVTimingLogger
from experiment.run.log import CountStreamEntry, CSVCountStreamLogger
from experiment.run.log import MarkersEntry, CSVMarkersLogger
from experiment.create.commands import ExecutorCommand, MeasuringCommand
from experiment.create.commands import DelayCommand, CompositeCommand, FileStatCommand
from experiment.create.commands import WaitMetricsCommand
from experiment.create.commands import CountStreamPostCommand, TimedCommandPreCommand, PipefailPreCommand
from experiment.system_meter import SystemMeasurement

from .multimeter_device_manager import MultimeterDeviceManager
from .metrics_log_dispatcher import MetricsLogDispatcher
from .command_config_shuffle import command_config_shuffle


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
        self._count_stdout: Path | bool = False

    def with_timings(self) -> Self:
        self._with_timings = True
        return self

    def count_stdout(self, target: str | Path = None) -> Self:
        if target is None:
            self._count_stdout = True
        else:
            self._count_stdout = Path(target)
        return self

    def collect_file_stats(self, path: str) -> Self:
        self._file_stats.add(path)
        return self

    def done(self) -> ExecutionBuilder:
        markers_dispatcher = self._parent.allocate_markers_dispatcher()
        command = MeasuringCommand(markers_dispatcher, self._command, self._work_dir)

        if self._count_stdout:
            count_dispatcher = self._parent.allocate_count_stream_dispatcher()
            link = CountStreamPostCommand(self._count_stdout, count_dispatcher)
            command.append(link)
        if self._with_timings:
            timing_dispatcher = self._parent.allocate_timing_dispatcher()
            link = TimedCommandPreCommand(timing_dispatcher)
            command.prepend(link)

        if self._count_stdout or self._with_timings:
            command.prepend(PipefailPreCommand())

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


class MultimeterCoordinator:
    def __init__(self):
        self._device_managers: dict[str, MultimeterDeviceManager] = {}

    def get_device_manager(self, serial_number: str) -> MultimeterDeviceManager:
        if serial_number not in self._device_managers:
            self._device_managers[serial_number] = MultimeterDeviceManager(serial_number)
        return self._device_managers[serial_number]


class MeasurementExecutionConstructor(ExecutionConstructor, MeasurementExecutionBuilder):
    @dataclass(frozen=True)
    class Config:
        runs: int
        tag: str

    def __init__(self, parent: HostConstructor, host: SSHHost,
                 multimeter_dispatcher: LogDispatcher[ElectricalMeasurement],
                 config: MeasurementExecutionConstructor.Config):
        super().__init__(host)
        self._parent = parent
        self._config = config
        self._head_delay = None
        self._tail_delay = None
        self._log_dispatcher: dict[object, LogDispatcher] = {}
        self._log_dispatcher[ElectricalMeasurement] = multimeter_dispatcher

    def allocate_timing_dispatcher(self) -> LogDispatcher[TimingEntry]:
        if TimingEntry not in self._log_dispatcher:
            self._log_dispatcher[TimingEntry] = LogDispatcher[TimingEntry]()
        return self._log_dispatcher[TimingEntry]

    def allocate_markers_dispatcher(self) -> LogDispatcher[MarkersEntry]:
        if MarkersEntry not in self._log_dispatcher:
            self._log_dispatcher[MarkersEntry] = LogDispatcher[MarkersEntry]()
        return self._log_dispatcher[MarkersEntry]

    def allocate_count_stream_dispatcher(self) -> LogDispatcher[CountStreamEntry]:
        if CountStreamEntry not in self._log_dispatcher:
            self._log_dispatcher[CountStreamEntry] = LogDispatcher[CountStreamEntry]()
        return self._log_dispatcher[CountStreamEntry]

    def allocate_file_stats_dispatcher(self) -> LogDispatcher[FileStatsEntry]:
        if FileStatsEntry not in self._log_dispatcher:
            self._log_dispatcher[FileStatsEntry] = LogDispatcher[FileStatsEntry]()
        return self._log_dispatcher[FileStatsEntry]

    def with_head_delay(self, delay: int) -> Self:
        self._head_delay = delay
        return self

    def with_tail_delay(self, delay: int) -> Self:
        self._tail_delay = delay
        return self

    def execute_with(self, command: str) -> MeasuredCommandBuilder:
        return MeasuredCommandConstructor(self, command)

    def done(self) -> HostBuilder:
        log_providers: list[LogProvider] = []

        metrics_dispatcher = self._parent.collect_metrics
        if metrics_dispatcher:
            metrics_log_providers = self._create_metrics(metrics_dispatcher)
            log_providers.extend(metrics_log_providers)

        if ElectricalMeasurement in self._log_dispatcher:
            log_providers.append(self._create_multimeter_log_provider())
        if TimingEntry in self._log_dispatcher:
            log_providers.append(self._create_timing_log_provider())
        if FileStatsEntry in self._log_dispatcher:
            log_providers.append(self._create_file_stats_log_provider())
        if MarkersEntry in self._log_dispatcher:
            log_providers.append(self._create_markers_log_provider())
        if CountStreamEntry in self._log_dispatcher:
            log_providers.append(self._create_count_stream_log_provider())

        commands = self._commands[:]
        if self._head_delay:
            commands.insert(0, DelayCommand(self._head_delay, "head"))
        if self._tail_delay:
            commands.append(DelayCommand(self._tail_delay, "tail"))

        if metrics_dispatcher:
            commands.append(WaitMetricsCommand(metrics_dispatcher))

        command_configs = []
        for run in range(self._config.runs):
            command_config = MeasurementStep.CommandConfig(run=run, runs=self._config.runs, commands=commands,
                                                           tag=self._config.tag, log_providers=log_providers)
            command_configs.append(command_config)
        self._parent.add_command_configs(command_configs)

        return self._parent

    def _create_metrics(self, metrics_dispatcher: LogDispatcher[SystemMeasurement]) -> list[LogProvider]:
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

        return log_providers

    def _create_multimeter_log_provider(self) -> LogProvider:
        formatter_class, formatter_config = self._parent.formatter_info
        formatter = formatter_class(**formatter_config)
        log_factory: LoggerFactory = lambda resource_path: CSVMultimeterLogger(resource_path / "multimeter.csv",
                                                                               formatter)
        multimeter_dispatcher = self._log_dispatcher[ElectricalMeasurement]
        multimeter_log_provider = GenericLogProvider(multimeter_dispatcher, log_factory)
        return multimeter_log_provider

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

    def _create_markers_log_provider(self) -> LogProvider:
        formatter_class, formatter_config = self._parent.formatter_info
        formatter = formatter_class(**formatter_config)
        log_factory: LoggerFactory = lambda resource_path: CSVMarkersLogger(resource_path / "markers.csv", formatter)
        markers_dispatcher = self._log_dispatcher[MarkersEntry]
        log_provider = GenericLogProvider(markers_dispatcher, log_factory)
        return log_provider

    def _create_count_stream_log_provider(self) -> LogProvider:
        formatter_class, formatter_config = self._parent.formatter_info
        formatter = formatter_class(**formatter_config)
        log_factory: LoggerFactory = lambda resource_path: CSVCountStreamLogger(resource_path / "count_stdout.csv",
                                                                                formatter)
        count_streamdispatcher = self._log_dispatcher[CountStreamEntry]
        log_provider = GenericLogProvider(count_streamdispatcher, log_factory)
        return log_provider


class InitializationConstructor(CompositeConstructor, InitializationBuilder):
    def __init__(self, parent: HostConstructor, host: SSHHost):
        super().__init__()
        self._parent = parent
        self._host = host

    def upload(self, local: str | Path, remote: str | Path) -> Self:
        self._steps.append(UploadStep(self._host, Path(local), Path(remote)))
        return self

    def done(self) -> HostBuilder:
        self._parent.add_init_step(self._steps)
        return self._parent


class ShutdownConstructor(CompositeConstructor, ShutdownBuilder):
    def __init__(self, parent: HostConstructor, host: SSHHost):
        super().__init__()
        self._parent = parent
        self._host = host

    def delete(self, remote: str | Path) -> Self:
        self._steps.append(DeleteStep(self._host, Path(remote)))
        return self

    def download(self, remote: str | Path, local: str | Path) -> Self:
        self._steps.append(DownloadStep(self._host, Path(remote), Path(local)))
        return self

    def done(self) -> HostBuilder:
        self._parent.add_shutdown_step(self._steps)
        return self._parent


class HostConstructor(CompositeConstructor, HostBuilder):
    @dataclass(frozen=True)
    class Config:
        host: SSHHost
        shuffle_measurement_sets: bool
        show_progress: bool
        multimeter_coordinator: MultimeterCoordinator

    @dataclass
    class ExtraHostContext:
        init_steps: list[Step] = field(default_factory=list)
        shutdown_steps: list[Step] = field(default_factory=list)
        command_configs: list[MeasurementStep.CommandConfig] = field(default_factory=list)
        temp_delta: float | None = None
        temp_min_duration: float | None = None

    def __init__(self, parent: ExperimentConstructor, config: Config):
        super().__init__()
        self._parent = parent
        self._config = config
        self._tags: set[str] = set()
        self._measurement: MultimeterMeasurement | None = None
        self._multimeter_dispatcher = None
        self._context = HostConstructor.ExtraHostContext()

    @property
    def collect_metrics(self) -> MetricsLogDispatcher:
        return self._parent.collect_metrics

    def add_command_configs(self, command_configs: list[MeasurementStep.CommandConfig]) -> None:
        self._context.command_configs.extend(command_configs)

    @property
    def formatter_info(self) -> tuple[type, dict]:
        return self._parent.formatter_info

    def add_init_step(self, steps: List[Step]) -> None:
        self._context.init_steps.extend(steps)

    def add_shutdown_step(self, steps: List[Step]) -> None:
        self._context.shutdown_steps.extend(steps)

    def initialize(self) -> InitializationBuilder:
        return InitializationConstructor(self, self._config.host)

    def shutdown(self) -> ShutdownBuilder:
        return ShutdownConstructor(self, self._config.host)

    def with_warmup(self) -> WarmupExecutionBuilder:
        return WarmupExecutionConstructor(self, self._config.host)

    def measure_with_multimeter(self, serial_number: str) -> Self:
        if self._measurement:
            raise RuntimeError("multimeter for measurement already specified")
        device_manager = self._config.multimeter_coordinator.get_device_manager(serial_number)
        device = device_manager.get_device()
        self._multimeter_dispatcher = LogDispatcher[ElectricalMeasurement]()
        self._measurement = MultimeterMeasurement(device, self._multimeter_dispatcher)
        return self

    def control_temperature(self, temp_delta: float, min_duration: timedelta = timedelta(minutes=15)) -> Self:
        if not self._measurement:
            raise RuntimeError("no temperature input available")

        self._context.temp_delta = temp_delta
        self._context.temp_min_duration = min_duration
        return self

    def measure_runs(self, runs: int, tag: str = None) -> MeasurementExecutionBuilder:
        if tag is None:
            tag = ""
        if tag in self._tags:
            raise ValueError(f"a measurement with the tag '{tag}' already exists on this host")
        self._tags.add(tag)
        config = MeasurementExecutionConstructor.Config(runs=runs, tag=tag)

        if not self._measurement:
            raise RuntimeError("no multimeter for measurement available")

        return MeasurementExecutionConstructor(self, self._config.host, self._multimeter_dispatcher, config)

    def done(self) -> ExperimentBuilder:
        if "" in self._tags and len(self._tags) > 1:
            raise ValueError("each measurement must have an distinctive tag")

        steps = []
        metrics_dispatcher = self._parent.collect_metrics
        if metrics_dispatcher:
            steps.append(TimeDeltaStep(self._config.host))
            steps.append(SystemMetricsClientStep(self._config.host, metrics_dispatcher))

        steps.extend(self._steps)
        if self._context.temp_delta is not None:
            max_temp_delta = self._context.temp_delta
            monitor_step = TempMonitorStep(self._multimeter_dispatcher, max_temp_delta, self._context.temp_min_duration)
            steps.append(monitor_step)
        else:
            monitor_step = None

        if self._context.command_configs:
            if self._config.shuffle_measurement_sets:
                command_configs = command_config_shuffle(self._context.command_configs)
            else:
                command_configs = self._context.command_configs[:]
            aborter = monitor_step
            temp_log_provider = self._create_temperature_log_provider()
            config = MeasurementStep.Config(show_progress=self._config.show_progress, command_configs=command_configs,
                                            log_providers=[temp_log_provider])
            step = MeasurementStep(self._config.host, self._measurement, config, aborter)

            steps.append(step)

        self._parent.add_steps(self._context.init_steps)
        self._parent.add_steps(steps)
        self._parent.add_steps(self._context.shutdown_steps)
        return self._parent

    def _create_temperature_log_provider(self) -> LogProvider:
        formatter_class, formatter_config = self._parent.formatter_info
        formatter = formatter_class(**formatter_config)

        def temp_logger_factory(path: Path):
            log_folder = path / self._config.host.host_name
            log_folder.mkdir(parents=True, exist_ok=True)
            return CSVTemperatureLogger(log_folder / "temperature.csv", formatter)

        log_provider = GenericLogProvider(self._multimeter_dispatcher, temp_logger_factory)
        return log_provider


class ExperimentConstructor(CompositeConstructor, ExperimentBuilder):
    @dataclass(frozen=True)
    class Arguments:
        ssh_user: str
        shuffle_measurement_sets: bool
        show_progress: bool

    def __init__(self, formatter_info: tuple[type, dict], connection_factory: ConnectionFactory, arguments: Arguments):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._metrics_dispatcher = None
        self._init_steps: List[InitStep] = []
        self._formatter_info = formatter_info
        self._connection_factory = connection_factory
        self._arguments = arguments
        self._multimeter_coordinator = MultimeterCoordinator()

    @property
    def collect_metrics(self) -> MetricsLogDispatcher:
        return self._metrics_dispatcher

    @property
    def formatter_info(self) -> tuple[type, dict]:
        return self._formatter_info

    def add_init_steps(self, init_steps: List[InitStep]):
        self._init_steps.extend(init_steps)

    def on_host(self, host_name: str, host: str) -> HostBuilder:
        ssh_host = SSHHost(host_name=host_name, host=host, ssh_user=self._arguments.ssh_user)
        self._init_steps.append(HostnameValidationStep(ssh_host))
        self._init_steps.append(HostnameInfoStep(ssh_host))
        config = HostConstructor.Config(host=ssh_host,
                                        shuffle_measurement_sets=self._arguments.shuffle_measurement_sets,
                                        show_progress=self._arguments.show_progress,
                                        multimeter_coordinator=self._multimeter_coordinator
                                        )
        return HostConstructor(self, config=config)

    def with_metrics_collection(self) -> Self:
        self._metrics_dispatcher = MetricsLogDispatcher()
        return self

    def build(self) -> ExperimentExecutor:
        experiment = ExperimentExecutor(self._connection_factory, self._init_steps, self._steps,
                                        self._metrics_dispatcher)
        return experiment
