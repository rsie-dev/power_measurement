import logging

from fastapi import FastAPI
import uvicorn

from .metrics import MeasurementSingle


app = FastAPI()

logger = logging.getLogger('uvicorn.error')
logger.setLevel(logging.DEBUG)

counter = 0


@app.post("/measurement/single/")
def add_line(measurement: MeasurementSingle) -> MeasurementSingle:
    global counter
    counter = counter + 1
    logger.info("received measurement %d\n%s" % (counter, measurement))
    return measurement


def server_main(args) -> None:
    uvicorn.run(app, host="192.168.1.201", port=10000, log_level="debug", reload=False)
