from __future__ import annotations
from typing import Self
from abc import ABC, abstractmethod
from pathlib import Path

from .experiment import Experiment


class Builder(ABC):
    pass


class CommandBuilder(Builder):
    @abstractmethod
    def with_work_dir(self, folder: str) -> Self:
        pass

    @abstractmethod
    def done(self) -> ExecutionBuilder:
        pass


class MeasuredCommandBuilder(CommandBuilder):
    @abstractmethod
    def with_timings(self) -> Self:
        pass

    @abstractmethod
    def collect_file_stats(self, path: str) -> Self:
        pass


class ExecutionBuilder(Builder):
    @abstractmethod
    def execute(self, command: str) -> Self:
        pass

    @abstractmethod
    def execute_with(self, command: str) -> CommandBuilder:
        pass


class WarmupExecutionBuilder(ExecutionBuilder):
    @abstractmethod
    def done(self) -> HostBuilder:
        pass


class MeasurementExecutionBuilder(ExecutionBuilder):
    @abstractmethod
    def with_multimeter(self, serial_number: str) -> Self:
        pass

    @abstractmethod
    def with_head_delay(self, delay: int) -> Self:
        pass

    @abstractmethod
    def with_tail_delay(self, delay: int) -> Self:
        pass

    @abstractmethod
    def execute_with(self, command: str) -> MeasuredCommandBuilder:
        pass

    @abstractmethod
    def done(self) -> HostBuilder:
        pass


class HostBuilder(Builder):
    @abstractmethod
    def upload(self, local: str | Path, remote: str | Path) -> Self:
        pass

    @abstractmethod
    def delete(self, remote: str | Path) -> Self:
        pass

    @abstractmethod
    def with_warmup(self) -> WarmupExecutionBuilder:
        pass

    @abstractmethod
    def measure_runs(self, runs: int, tag: str = None) -> MeasurementExecutionBuilder:
        pass

    @abstractmethod
    def done(self) -> ExperimentBuilder:
        pass


class ExperimentBuilder(Builder):
    @abstractmethod
    def with_metrics_collection(self) -> Self:
        pass

    @abstractmethod
    def on_host(self, host_name: str, host: str) -> HostBuilder:
        pass

    @abstractmethod
    def build(self) -> Experiment:
        pass
