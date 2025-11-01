import logging
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI

from .metrics import SystemMeasurement, Metrics
from .measurement_logger import MeasurementLogger

logger = logging.getLogger('system_meter.main')


def create_app(measurement_logger: MeasurementLogger, startup_call_back: Callable):
    @asynccontextmanager
    async def lifespan(app: FastAPI):  # pylint: disable=unused-argument
        startup_call_back()
        yield

    app = FastAPI(lifespan=lifespan)

    @app.post("/measurement/single/")
    def add_line(measurement: SystemMeasurement) -> SystemMeasurement:
        measurement_logger.log(measurement)
        return measurement

    @app.post("/measurement/batch/")
    def add_batch(metrics: Metrics) -> Metrics:
        for measurement in metrics.metrics:
            measurement_logger.log(measurement)
        return metrics

    return app
