import logging
import datetime

import ntplib
import humanize

from .experiment_runtime import ExperimentRuntime
from .step import Step


class TimeDeltaStep(Step):
    def __init__(self, host_name: str, host: str):
        super().__init__("time delta")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host_name = host_name
        self._host = host

    def execute(self, runtime: ExperimentRuntime):
        self._get_ntp_delta()

    def _get_ntp_delta(self):
        ntp_client = ntplib.NTPClient()
        self._logger.debug("get time diff to: %s", self._host)
        response = ntp_client.request(self._host, version=4)  # v4 is common
        offset_delta = datetime.timedelta(seconds = response.offset)
        status = "behind" if response.offset < 0 else "ahead"
        delta_str = humanize.precisedelta(offset_delta, minimum_unit="microseconds")
        self._logger.info("Host %s is %s %s", self._host, status, delta_str)
        return offset_delta
