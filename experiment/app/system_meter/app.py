import logging
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI

from app.run.log import Logger
from .metrics import SystemMeasurement, Metrics


logger = logging.getLogger('system_meter.main')


def create_app(measurement_logger: Logger[SystemMeasurement], startup_call_back: Callable):
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
        measurement_logger.log(metrics.metrics)
        return metrics

    return app
