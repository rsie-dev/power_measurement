import logging
from pathlib import Path
from contextlib import contextmanager
import importlib

from ruamel.yaml import YAML

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
        formatter_info = self._get_formatter_info()
        formatter_class, formatter_config = formatter_info
        formatter = formatter_class(**formatter_config)
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        yield
        logging.getLogger().removeHandler(handler)

    def _get_formatter_info(self) -> tuple[type, dict]:
        config = self._get_logging_config().copy()
        config_file_formatter = config["formatters"]["file"]
        config_file_formatter["fmt"] = config_file_formatter.pop("format")
        formatter_class = self._get_formatter_class(config_file_formatter)
        return (formatter_class, config_file_formatter)

    def _get_formatter_class(self, config: dict) -> type:
        if "()" in config:
            cls_path = config.pop("()")
            module_path, class_name = cls_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            formatter_class = getattr(module, class_name)
            return formatter_class
        return logging.Formatter

    def _get_logging_config(self):
        folder = self._get_app_folder()
        config = folder / 'logging.yaml'
        with open(config, "rt", encoding="UTF_8") as f:
            yaml = YAML(typ="safe")
            return yaml.load(f)

    def _get_app_folder(self):
        script = Path(__file__).resolve()
        folder = script.parent.parent
        return folder
