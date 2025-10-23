import logging

from fastapi import FastAPI
import uvicorn

from .metrics import Measurement, Metrics


app = FastAPI()

logger = logging.getLogger('server.main')

counter = 0


@app.post("/measurement/single/")
def add_line(measurement: Measurement) -> Measurement:
    global counter
    counter = counter + 1
    logger.info("received measurement %d\n%s" % (counter, measurement))
    return measurement


batch_counter = 0


@app.post("/measurement/batch/")
def add_batch(metrics: Metrics) -> Metrics:
    global batch_counter
    batch_counter = batch_counter + 1
    logger.info("received batch %d" % (batch_counter, ))
    return metrics


def server_main(args) -> None:
    uvicorn.run(app, host="192.168.1.201", port=10000, log_config=None, log_level=None, reload=False)
