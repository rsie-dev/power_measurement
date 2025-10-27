import logging

from fastapi import FastAPI

from .metrics import SystemMeasurement, Metrics
from .measurement_logger import MeasurementLogger

logger = logging.getLogger('server.main')


def create_app(measurement_logger: MeasurementLogger):
    app = FastAPI()

    counter = 0

    @app.post("/measurement/single/")
    def add_line(measurement: SystemMeasurement) -> SystemMeasurement:
        nonlocal counter
        counter = counter + 1
        logger.info("received measurement %d\n%s" % (counter, measurement))
        measurement_logger.log(measurement)
        return measurement

    batch_counter = 0

    @app.post("/measurement/batch/")
    def add_batch(metrics: Metrics) -> Metrics:
        nonlocal batch_counter
        batch_counter = batch_counter + 1
        logger.info("received batch %d" % (batch_counter, ))
        for measurement in metrics.metrics:
            measurement_logger.log(measurement)
        return metrics

    return app
