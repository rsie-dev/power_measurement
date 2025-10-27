import logging

from fastapi import FastAPI

from .metrics import Measurement, Metrics

logger = logging.getLogger('server.main')


def create_app():
    app = FastAPI()

    counter = 0

    @app.post("/measurement/single/")
    def add_line(measurement: Measurement) -> Measurement:
        nonlocal counter
        counter = counter + 1
        logger.info("received measurement %d\n%s" % (counter, measurement))
        return measurement

    batch_counter = 0

    @app.post("/measurement/batch/")
    def add_batch(metrics: Metrics) -> Metrics:
        nonlocal batch_counter
        batch_counter = batch_counter + 1
        logger.info("received batch %d" % (batch_counter, ))
        return metrics

    return app
