import logging
from contextlib import contextmanager
from concurrent.futures import Executor

from app.experiment.base import ExperimentEnvironment
from .measurement import Measurement


logger = logging.getLogger(__name__)


@contextmanager
def measure(measurement: Measurement, environment: ExperimentEnvironment, executor: Executor):
    logger.info("Start measurement: %s", measurement.name)
    measurement.start(environment, executor)
    try:
        yield measurement
    finally:
        logger.info("Stop measurement: %s", measurement.name)
        measurement.stop(environment)
