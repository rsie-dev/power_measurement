import logging
from pathlib import Path
from contextlib import contextmanager

from .experiment_loader import ExperimentLoader


class Runner:
    def __init__(self, resources: Path, formatter_info: tuple[type, dict]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._resources = resources
        self._formatter_info = formatter_info

    def run_experiment(self, args):
        experiment_loader = ExperimentLoader()
        experiment_module = Path(args.experiment[0])
        experiment = experiment_loader.load_steps_from_path(experiment_module)
        resources = self._resources / experiment_module.stem
        self._logger.info("experiment resources: %s", resources.relative_to(Path.cwd()))
        resources.mkdir(parents=True, exist_ok=True)
        with self._add_logfile(resources / "experiment.log"):
            self._logger.info("Experiment start: %s", experiment_module.stem)
            try:
                metrics_server_address = (args.host, args.port)
                experiment.run(resources, metrics_server_address)
            finally:
                self._logger.info("Experiment finished: %s", experiment_module.stem)

    @contextmanager
    def _add_logfile(self, logfile: Path):
        handler = logging.FileHandler(logfile, mode="w")
        handler.setLevel(logging.DEBUG)
        formatter_class, formatter_config = self._formatter_info
        formatter = formatter_class(**formatter_config)
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        yield
        logging.getLogger().removeHandler(handler)
