import logging

from fastapi import FastAPI

from .metrics import SystemMeasurement, Metrics
from .measurement_logger import MeasurementLogger

logger = logging.getLogger('server.main')


def create_app(measurement_logger: MeasurementLogger):
    app = FastAPI()

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
