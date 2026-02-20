from __future__ import annotations
from typing import Optional
from typing import Self
from abc import ABC, abstractmethod

from .command import Command
from .experiment import Experiment


class Builder(ABC):
    pass


class CommandBuilder(Builder):
    @abstractmethod
    def with_work_dir(self, folder: str) -> Self:
        pass

    @abstractmethod
    def with_timing(self) -> Self:
        pass

    @abstractmethod
    def done(self) -> HostCommandBuilder:
        pass


class HostCommandBuilder(Builder):
    @abstractmethod
    def execute(self, command: str) -> Self:
        pass

    @abstractmethod
    def execute_with(self, command: str) -> CommandBuilder:
        pass

    @abstractmethod
    def add_command(self, command: Command) -> None:
        pass

    @abstractmethod
    def done(self) -> HostBuilder:
        pass


class HostBuilder(Builder):
    @abstractmethod
    def with_usb_meter(self, serial_number: str) -> Self:
        pass

    @abstractmethod
    def measure_commands(self) -> HostCommandBuilder:
        pass

    @abstractmethod
    def done(self) -> RunsBuilder:
        pass


class RunsBuilder(Builder):
    @abstractmethod
    def on_host(self, host_name: str, host: str, ssh_user: Optional[str] = None) -> HostBuilder:
        pass

    @abstractmethod
    def done(self) -> ExperimentBuilder:
        pass


class ExperimentBuilder(Builder):
    @abstractmethod
    def execute_runs(self, runs: int) -> RunsBuilder:
        pass

    @abstractmethod
    def with_metrics_collection(self) -> Self:
        pass

    @abstractmethod
    def build(self) -> Experiment:
        pass
