from __future__ import annotations
import logging
from typing import List, Optional
from typing import Self

from .steps import Step, RegisterForSystemMetricsStep, StartSystemMetricsClientStep, USBMeterStep, HostCommandStep
from .experiment import Experiment


class Builder:
    pass


class CompositeBuilder(Builder):
    def __init__(self):
        self._steps: List[Step] = []

    def add_steps(self, steps: List[Step]) -> None:
        self._steps.extend(steps)


class NodeCommandBuilder(Builder):
    def __init__(self, parent: HostBuilder, host_name: str, ssh_user: str):
        self._parent = parent
        self._host_name = host_name
        self._ssh_user = ssh_user
        self._use_metrics_server = False
        self._commands = []

    def log_metrics(self) -> Self:
        self._use_metrics_server = True
        return self

    def execute(self, command) -> Self:
        self._commands.append(command)
        return self

    def done(self) -> HostBuilder:
        steps = []
        if self._use_metrics_server:
            step = RegisterForSystemMetricsStep(self._parent.host)
            steps.append(step)
            step = StartSystemMetricsClientStep(self._host_name, self._ssh_user)
            steps.append(step)
        step = HostCommandStep(self._host_name, self._ssh_user, self._commands)
        steps.append(step)
        self._parent.add_steps(steps)
        return self._parent


class HostBuilder(CompositeBuilder):
    def __init__(self, parent: ExperimentBuilder, host: str):
        super().__init__()
        self._parent = parent
        self._host = host
        self._serial_number = None

    @property
    def host(self) -> str:
        return self._host

    def log_usb_meter(self, serial_number: str) -> Self:
        self._serial_number = serial_number
        return self

    def on_node(self, host_name: str, ssh_user: Optional[str] = None) -> NodeCommandBuilder:
        ssh_user = ssh_user or "dietpi"
        return NodeCommandBuilder(self, host_name, ssh_user)

    def done(self) -> ExperimentBuilder:
        steps = []
        if self._serial_number:
            step = USBMeterStep(self._host, self._serial_number)
            steps.append(step)
        steps.extend(self._steps)
        self._parent.add_steps(steps)
        return self._parent


class ExperimentBuilder(CompositeBuilder):
    def __init__(self):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)

    def on_host(self, host: str) -> HostBuilder:
        return HostBuilder(self, host)

    def build(self) -> Experiment:
        experiment = Experiment(self._steps)
        return experiment
