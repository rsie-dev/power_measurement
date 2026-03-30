from typing import Optional
from .experiment import Experiment
from .command import Command
from .api import Builder
from .api import CommandBuilder, MeasuredCommandBuilder
from .api import ExperimentBuilder, HostBuilder, MeasurementExecutionBuilder, WarmupExecutionBuilder, ExecutionBuilder
from .api import InitializationBuilder, ShutdownBuilder


__all__ = [
    "Experiment", "Command",
    "Builder",
    "ExperimentBuilder",
    "CommandBuilder", "MeasuredCommandBuilder",
    "HostBuilder", "MeasurementExecutionBuilder", "WarmupExecutionBuilder", "ExecutionBuilder",
    "InitializationBuilder", "ShutdownBuilder",
    "get_experiment_builder", "set_experiment_builder",
]


class ExperimentConfig:
    constructor: Optional[Builder] = None


def get_experiment_builder() -> Builder:
    return ExperimentConfig.constructor


def set_experiment_builder(builder: Builder) -> None:
    ExperimentConfig.constructor = builder
