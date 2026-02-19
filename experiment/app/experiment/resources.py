from pathlib import Path

from .steps.experiment_resources import ExperimentResources


class Resources(ExperimentResources):
    def __init__(self, resources_path: Path):
        self._resources_path = resources_path

    def electrical_resources_path(self) -> Path:
        return self._resources_path

    def metrics_resources_path(self) -> Path:
        return self._resources_path

    def timings_resources_path(self) -> Path:
        return self._resources_path
