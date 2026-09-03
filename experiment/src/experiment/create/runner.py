import logging
from pathlib import Path
from contextlib import contextmanager
import shutil
import datetime as dt

import humanize

from experiment.ssh import ConnectionFactory
from experiment._version import version, commit_id
from .experiment_loader import ExperimentLoader
from .user_connection_factory import PasswordConnectionFactory, PrivateKeyConnectionFactory


class Runner:
    def __init__(self, resources: Path, formatter_info: tuple[type, dict]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._resources = resources
        self._formatter_info = formatter_info

    def run_experiment(self, args):
        experiment_loader = ExperimentLoader(self._formatter_info)
        experiment_module = Path(args.experiment[0])
        connection_factory = self._create_connection_factory(args)
        experiment = experiment_loader.load_experiment_from_path(experiment_module, connection_factory, args)
        self._resources.mkdir(parents=True, exist_ok=True)
        resources = self._resources / experiment_module.stem
        self._logger.info("Experiment resource path: %s", resources.relative_to(Path.cwd()))
        resources.mkdir()
        self._logger.debug("copy experiment module to resource folder")
        shutil.copy(experiment_module.resolve(), resources / experiment_module.name)
        with self._add_logfile(resources / "experiment.log"):
            self._log_version_info()
            self._do_run(experiment_module, args, experiment, resources)

    def _do_run(self, experiment_module: Path, args, experiment, resources: Path):
        self._logger.info("Experiment start: %s", experiment_module.stem)
        metrics_server_address = (args.host, args.port)
        start = dt.datetime.now()
        try:
            experiment.run(resources, metrics_server_address)
        finally:
            elapsed = dt.datetime.now() - start
            elapsed_seconds = dt.timedelta(seconds=int(elapsed.total_seconds()))
            elapsed_str = humanize.precisedelta(elapsed_seconds, minimum_unit="seconds")
            self._logger.info("Experiment finished in %s: %s", elapsed_str, experiment_module.stem)

    def _create_connection_factory(self, args) -> ConnectionFactory:
        if args.ssh_key:
            return PrivateKeyConnectionFactory(args.ssh_key)
        return PasswordConnectionFactory()

    @contextmanager
    def _add_logfile(self, logfile: Path):
        handler = logging.FileHandler(logfile, mode="w")
        handler.setLevel(logging.DEBUG)
        formatter_class, formatter_config = self._formatter_info
        formatter = formatter_class(**formatter_config)
        handler.setFormatter(formatter)
        file_logger = ["", "paramiko.transport"]
        for logger in file_logger:
            logging.getLogger(logger).addHandler(handler)
        yield
        for logger in file_logger:
            logging.getLogger(logger).removeHandler(handler)

    def _log_version_info(self):
        self._logger.debug("power-measurement-experiment version: v%s (%s)", version, commit_id)
