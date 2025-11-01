import logging
from pathlib import Path

from .experiment_loader import ExperimentLoader


class Runner:
    def __init__(self, resources: Path):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._resources = resources

    def run_experiment(self, args):
        experiment_loader = ExperimentLoader()
        experiment_module = Path(args.experiment[0])
        experiment = experiment_loader.load_steps_from_path(experiment_module)
        resources = self._resources / experiment_module.stem
        self._logger.info("experiment resources: %s", resources.relative_to(Path.cwd()))
        resources.mkdir(parents=True, exist_ok=True)
        self._logger.info("Experiment start: %s", experiment_module.stem)
        try:
            experiment.run(resources)
        finally:
            self._logger.info("Experiment finished: %s", experiment_module.stem)
