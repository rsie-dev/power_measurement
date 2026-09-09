from __future__ import annotations

from datetime import timedelta
import logging
from typing import List, Self
from dataclasses import dataclass, field
from pathlib import Path
import random

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
from experiment.run.steps import WarmupCommandStep
from experiment.run.steps import MeasurementStep, MeasurementAbortMonitor
from experiment.run.steps import HostnameValidationStep, HostnameInfoStep
from experiment.run.steps import UploadStep, DownloadStep, DeleteStep
from experiment.run.steps import TempMonitorStep, DisableTimersStep
from experiment.run.steps import SBCTemperatureMonitorStep
from experiment.run.steps import TempSensorStep
from experiment.run.steps.measurement import MultimeterMeasurement
from experiment.run.experiment_executor import ExperimentExecutor
from experiment.run.log import LogProvider, LoggerFactory, GenericLogProvider, LogDispatcher
from experiment.run.log import MetricType, CSVMetricsLogger
from experiment.run.log import CSVMultimeterLogger
from experiment.run.log import CSVTemperatureLogger, TemperatureEntry
from experiment.run.log import FileStatsEntry, CSVFileStatLogger
from experiment.run.log import TimingEntry, CSVTimingLogger
from experiment.run.log import CountStreamEntry, CSVCountStreamLogger
from experiment.run.log import MarkersEntry, CSVMarkersLogger
from experiment.create.commands import ExecutorCommand, MeasuringCommand, ClearCacheCommand
from experiment.create.commands import CompositeCommand, FileStatCommand
from experiment.create.commands import DelayCommand, StableTemperatureDelayCommand
from experiment.create.commands import WaitMetricsCommand
from experiment.create.commands import CountStreamPostCommand, TimedCommandPreCommand, PipefailPreCommand
from experiment.system_meter import SystemMeasurement
from experiment.sensor import get_sensor_device

from .multimeter_device_manager import MultimeterDeviceManager
from .metrics_log_dispatcher import MetricsLogDispatcher
from .command_config_shuffle import command_config_shuffle
from .ambient_temp_log_dispatcher import AmbientTempLogDispatcher

class Constructor(Builder):
    pass


class CompositeConstructor(Constructor):
    def __init__(self):
        super().__init__()
        self._steps: List[Step] = []

    def add_steps(self, steps: List[Step]) -> None:
        self._steps.extend(steps)


class CommandConstructor(Constructor, CommandBuilder):
    DEFAULT_SHELL = "/bin/sh"

    def __init__(self, parent: ExecutionConstructor, command: str):
        super().__init__()
        self._parent = parent
        self._command = command
        self._work_dir = None
        self._shell = self.DEFAULT_SHELL

    def with_work_dir(self, folder: str) -> Self:
        self._work_dir = folder
        return self

    def with_shell(self, shell: str) -> Self:
        self._shell = shell
        return self

    def done(self) -> ExecutionBuilder:
        command = ExecutorCommand(self._command, self._shell, self._work_dir)
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
        command = MeasuringCommand(markers_dispatcher, self._command, self._shell, self._work_dir)

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
        self.add_command(ExecutorCommand(command, CommandConstructor.DEFAULT_SHELL))
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
        clear_cache: bool
        sbc_temp_dispatcher: LogDispatcher[TemperatureEntry]

    @dataclass(frozen=True)
    class Delay:
        min_delay: timedelta
        max_delay: timedelta
        slope_threshold: float | None = None

    def __init__(self, parent: HostConstructor, host: SSHHost,
                 multimeter_dispatcher: LogDispatcher[ElectricalMeasurement],
                 config: MeasurementExecutionConstructor.Config):
        super().__init__(host)
        self._parent = parent
        self._config = config
        self._head_delay: MeasurementExecutionConstructor.Delay | None = None
        self._tail_delay: MeasurementExecutionConstructor.Delay | None = None
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
        head_delay = MeasurementExecutionConstructor.Delay(
            min_delay=timedelta(seconds=delay),
            max_delay=timedelta(seconds=delay),
        )
        self._head_delay = head_delay
        return self

    def with_tail_delay(self, delay: int) -> Self:
        tail_delay = MeasurementExecutionConstructor.Delay(
            min_delay=timedelta(seconds=delay),
            max_delay=timedelta(seconds=delay),
        )
        self._tail_delay = tail_delay
        return self

    def with_stable_temp_head_delay(self, min_delay: int, max_delay: int, threshold: float = 0.05) -> Self:
        if not self._config.sbc_temp_dispatcher:
            raise RuntimeError("no SBC temperature available")

        head_delay = MeasurementExecutionConstructor.Delay(
            min_delay=timedelta(seconds=min_delay),
            max_delay=timedelta(seconds=max_delay),
            slope_threshold=threshold,
        )
        self._head_delay = head_delay
        return self

    def with_stable_temp_tail_delay(self, min_delay: int, max_delay: int, threshold: float = 0.05) -> Self:
        tail_delay = MeasurementExecutionConstructor.Delay(
            min_delay=timedelta(seconds=min_delay),
            max_delay=timedelta(seconds=max_delay),
            slope_threshold=threshold,
        )
        self._tail_delay = tail_delay
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
        if self._config.clear_cache:
            commands.insert(0, ClearCacheCommand())

        if self._head_delay:
            command = self._create_delay_command("head", self._head_delay)
            commands.insert(0, command)
        if self._tail_delay:
            command = self._create_delay_command("tail", self._tail_delay)
            commands.append(command)

        if metrics_dispatcher:
            commands.append(WaitMetricsCommand(metrics_dispatcher))

        command_configs = []
        for run in range(self._config.runs):
            command_config = MeasurementStep.CommandConfig(run=run, runs=self._config.runs, commands=commands,
                                                           tag=self._config.tag, log_providers=log_providers)
            command_configs.append(command_config)
        self._parent.add_command_configs(command_configs)

        return self._parent

    def _create_delay_command(self, kind: str, delay: Delay) -> Command:
        if delay.slope_threshold is None:
            return DelayCommand(delay.min_delay, kind)
        config = StableTemperatureDelayCommand.Config(
            min_delay=delay.min_delay,
            max_delay=delay.max_delay,
            slope_threshold=delay.slope_threshold,
            kind=kind,
            temp_dispatcher=self._config.sbc_temp_dispatcher,
        )
        return StableTemperatureDelayCommand(config)

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
        show_progress: bool
        multimeter_coordinator: MultimeterCoordinator
        rng: random.Random | None

    @dataclass
    class ExtraHostContext:
        init_steps: list[Step] = field(default_factory=list)
        shutdown_steps: list[Step] = field(default_factory=list)
        command_configs: list[MeasurementStep.CommandConfig] = field(default_factory=list)
        temp_delta: float | None = None
        temp_min_duration: timedelta | None = None
        clear_cache: bool = False
        disable_timers: bool = False

    @dataclass
    class SBCContext:
        update_interval: float | None = None

    @dataclass
    class TemperatureContext:
        serial_device: str | None = None
        temp_offset: float= 0

    @dataclass
    class Dispatcher:
        multimeter_dispatcher: LogDispatcher[ElectricalMeasurement] | None = None
        ambient_temp_dispatcher: LogDispatcher[TemperatureEntry] | None = None
        sbc_temp_dispatcher: LogDispatcher[TemperatureEntry] | None = None

    def __init__(self, parent: ExperimentConstructor, config: Config):
        super().__init__()
        self._parent = parent
        self._config = config
        self._tags: set[str] = set()
        self._measurement: MultimeterMeasurement | None = None
        self._dispatcher = HostConstructor.Dispatcher()
        self._context = HostConstructor.ExtraHostContext()
        self._temp_context = HostConstructor.TemperatureContext()
        self._sbc_context = HostConstructor.SBCContext()

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

    def with_sbc_monitoring(self, update_interval: float = 1) -> Self:
        self._sbc_context.update_interval = update_interval
        self._dispatcher.sbc_temp_dispatcher = LogDispatcher[TemperatureEntry]()
        return self

    def with_warmup(self) -> WarmupExecutionBuilder:
        return WarmupExecutionConstructor(self, self._config.host)

    def with_clear_cache(self) -> Self:
        self._context.clear_cache = True
        return self

    def measure_with_multimeter(self, serial_number: str) -> Self:
        if self._measurement:
            raise RuntimeError("multimeter for measurement already specified")
        device_manager = self._config.multimeter_coordinator.get_device_manager(serial_number)
        self._dispatcher.multimeter_dispatcher = LogDispatcher[ElectricalMeasurement]()
        config = MultimeterMeasurement.Config(
            device_manager=device_manager,
            log_dispatcher=self._dispatcher.multimeter_dispatcher,
        )
        self._measurement = MultimeterMeasurement(config)
        return self

    def with_ambient_temperature_multimeter(self, serial_number: str, temp_offset: float = 0) -> Self:
        if not self._measurement:
            raise RuntimeError("no multimeter for measurement specified")
        if serial_number != self._measurement.serial_number:
            raise ValueError("serial number for multimeter temperature must match multimeter serial number")
        if self._dispatcher.ambient_temp_dispatcher:
            raise RuntimeError("ambient temperature input already specified")

        self._dispatcher.ambient_temp_dispatcher = AmbientTempLogDispatcher()
        self._dispatcher.multimeter_dispatcher.register_logger(self._dispatcher.ambient_temp_dispatcher)
        self._measurement.set_temp_offset(temp_offset)

        return self

    def with_ambient_temperature_sensor(self, serial_device: str, temp_offset: float = 0) -> Self:
        if self._dispatcher.ambient_temp_dispatcher:
            raise RuntimeError("ambient temperature input already specified")
        self._dispatcher.ambient_temp_dispatcher = LogDispatcher[TemperatureEntry]()
        self._temp_context.serial_device = serial_device
        self._temp_context.temp_offset = temp_offset
        return self

    def control_temperature(self, temp_delta: float, min_duration: timedelta = timedelta(minutes=15)) -> Self:
        if not self._dispatcher.ambient_temp_dispatcher:
            raise RuntimeError("no ambient temperature input available")

        self._context.temp_delta = temp_delta
        self._context.temp_min_duration = min_duration
        return self

    def disable_timers(self) -> Self:
        self._context.disable_timers = True
        return self

    def measure_runs(self, runs: int, tag: str = None) -> MeasurementExecutionBuilder:
        if tag is None:
            tag = ""
        if tag in self._tags:
            raise ValueError(f"a measurement with the tag '{tag}' already exists on this host")
        self._tags.add(tag)
        config = MeasurementExecutionConstructor.Config(
            runs=runs,
            tag=tag,
            clear_cache=self._context.clear_cache,
            sbc_temp_dispatcher=self._dispatcher.sbc_temp_dispatcher,
        )

        if not self._measurement:
            raise RuntimeError("no multimeter for measurement available")

        return MeasurementExecutionConstructor(self, self._config.host, self._dispatcher.multimeter_dispatcher, config)

    def done(self) -> ExperimentBuilder:
        if "" in self._tags and len(self._tags) > 1:
            raise ValueError("each measurement must have an distinctive tag")

        steps = []
        if self._temp_context.serial_device:
            sensor_device = get_sensor_device(self._temp_context.serial_device)
            config = TempSensorStep.Config(
                sensor_device=sensor_device,
                log_dispatcher=self._dispatcher.ambient_temp_dispatcher,
                temp_offset=self._temp_context.temp_offset,
            )
            temp_sensor_step = TempSensorStep(config)
            steps.append(temp_sensor_step)
        else:
            temp_sensor_step = None

        if self._dispatcher.sbc_temp_dispatcher:
            log_provider = self._create_sbc_temperature_log_provider()
            config = SBCTemperatureMonitorStep.Config(
                host=self._config.host,
                sbc_temp_dispatcher=self._dispatcher.sbc_temp_dispatcher,
                log_provider=log_provider,
                update_interval=self._sbc_context.update_interval
            )
            steps.append(SBCTemperatureMonitorStep(config))

        metrics_dispatcher = self._parent.collect_metrics
        if metrics_dispatcher:
            steps.append(TimeDeltaStep(self._config.host))
            steps.append(SystemMetricsClientStep(self._config.host, metrics_dispatcher))

        if self._context.disable_timers:
            steps.append(DisableTimersStep(self._config.host))

        steps.extend(self._steps)
        if self._context.temp_delta is not None:
            config = TempMonitorStep.Config(
                kind="ambient",
                log_dispatcher=self._dispatcher.ambient_temp_dispatcher,
                max_temp_delta=self._context.temp_delta,
                min_duration=self._context.temp_min_duration,
            )
            monitor_step = TempMonitorStep(config)
            steps.append(monitor_step)
        else:
            monitor_step = None

        if self._context.command_configs:
            if self._config.rng:
                command_configs = command_config_shuffle(self._context.command_configs, rng=self._config.rng)
            else:
                command_configs = self._context.command_configs[:]
            aborter = MeasurementAbortMonitor()
            if temp_sensor_step:
                aborter.add_aborter(temp_sensor_step)
            if monitor_step:
                aborter.add_aborter(monitor_step)
            if self._measurement:
                aborter.add_aborter(self._measurement)

            log_providers = []
            log_providers.append(self._create_ambient_temperature_log_provider())
            config = MeasurementStep.Config(show_progress=self._config.show_progress, command_configs=command_configs,
                                            log_providers=log_providers)
            step = MeasurementStep(self._config.host, self._measurement, config, aborter)

            steps.append(step)

        self._parent.add_steps(self._context.init_steps)
        self._parent.add_steps(steps)
        self._parent.add_steps(self._context.shutdown_steps)
        return self._parent

    def _create_ambient_temperature_log_provider(self) -> LogProvider:
        formatter_class, formatter_config = self._parent.formatter_info
        formatter = formatter_class(**formatter_config)

        def temp_logger_factory(path: Path):
            log_folder = path / self._config.host.host_name
            log_folder.mkdir(parents=True, exist_ok=True)
            ambient_logger = CSVTemperatureLogger(log_folder / "temperature_ambient.csv", formatter)
            return ambient_logger

        log_provider = GenericLogProvider(self._dispatcher.ambient_temp_dispatcher, temp_logger_factory)
        return log_provider

    def _create_sbc_temperature_log_provider(self) -> LogProvider:
        formatter_class, formatter_config = self._parent.formatter_info
        formatter = formatter_class(**formatter_config)

        def temp_logger_factory(path: Path):
            log_folder = path / self._config.host.host_name
            log_folder.mkdir(parents=True, exist_ok=True)
            logger = CSVTemperatureLogger(log_folder / "temperature_sbc.csv", formatter)
            return logger

        log_provider = GenericLogProvider(self._dispatcher.sbc_temp_dispatcher, temp_logger_factory)
        return log_provider


class ExperimentConstructor(CompositeConstructor, ExperimentBuilder):
    @dataclass(frozen=True)
    class Arguments:
        ssh_user: str
        rng: random.Random | None
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
                                        show_progress=self._arguments.show_progress,
                                        multimeter_coordinator=self._multimeter_coordinator,
                                        rng=self._arguments.rng,
                                        )
        return HostConstructor(self, config=config)

    def with_metrics_collection(self) -> Self:
        self._metrics_dispatcher = MetricsLogDispatcher()
        return self

    def build(self) -> ExperimentExecutor:
        experiment = ExperimentExecutor(self._connection_factory, self._init_steps, self._steps,
                                        self._metrics_dispatcher)
        return experiment
