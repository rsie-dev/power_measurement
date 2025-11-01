import logging
from pathlib import Path
from contextlib import contextmanager

from ruamel.yaml import YAML

from .experiment_loader import ExperimentLoader


class Runner:
    def __init__(self, resources: Path):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._resources = resources

    def _get_app_folder(self):
        script = Path(__file__).resolve()
        folder = script.parent.parent
        return folder

    def _get_logging_config(self):
        folder = self._get_app_folder()
        config = folder / 'logging.yaml'
        with open(config, "rt", encoding="UTF_8") as f:
            yaml = YAML(typ="safe")
            return yaml.load(f)

    @contextmanager
    def _add_logfile(self, logfile: Path):
        config = self._get_logging_config()
        handler = logging.FileHandler(logfile, mode="w")
        handler.setLevel(logging.DEBUG)
        config_file_formatter = config["formatters"]["file"]
        config_file_formatter["fmt"] = config_file_formatter.pop("format")
        formatter = logging.Formatter(**(dict(config_file_formatter)))
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        yield
        logging.getLogger().removeHandler(handler)

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
                experiment.run(resources)
            finally:
                self._logger.info("Experiment finished: %s", experiment_module.stem)
