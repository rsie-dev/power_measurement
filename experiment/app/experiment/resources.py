from pathlib import Path

from app.experiment.base import ExperimentResources


class Resources(ExperimentResources):
    def __init__(self, resources_path: Path):
        self._resources_path = resources_path

    def resources_path(self) -> Path:
        return self._resources_path
