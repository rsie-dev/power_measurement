import logging
import importlib.util
import importlib
import sys
from pathlib import Path
from typing import Optional

import app.api
from .constructor import ExperimentExecutor
from .constructor import ExperimentConstructor


class ExperimentLoader:
    def __init__(self, formatter_info: tuple[type, dict]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._formatter_info = formatter_info

    def load_experiment_from_path(self, path: Path, ssh_user: str,
                                  package_name: Optional[str] = None) -> ExperimentExecutor:
        """
        Import a .py file at `path` as a module and return the module object.
        - Uses a unique module name so you can load multiple different files or reload the same path.
        - The module itself should import pipeline_core.P to register steps, as in my_steps.py.
        """
        self._logger.info("Load experiment: %s", path.stem)
        if not path.exists():
            raise FileNotFoundError(path)

        app.api.EXPERIMENT_CONSTRUCTOR = ExperimentConstructor(self._formatter_info, ssh_user)

        unique_name = f"{package_name or ""}.{path.stem}"
        spec = importlib.util.spec_from_file_location(unique_name, path)
        if spec is None:
            raise ImportError(f"Cannot create spec for: {path}")
        module = importlib.util.module_from_spec(spec)

        # prepare the module namespace with the experiment API
        #module.Experiment = experiment_api

        # Execute the module
        loader = spec.loader
        assert loader is not None
        loader.exec_module(module)

        # Place it in sys.modules so debugging and traceback show a module name
        sys.modules[unique_name] = module

        experiment = getattr(module, "experiment")
        return experiment
