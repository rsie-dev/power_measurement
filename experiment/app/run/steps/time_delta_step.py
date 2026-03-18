import logging
import datetime

import ntplib
import humanize
import isodate

from app.common import Host
from app.run.base import ExperimentEnvironment
from app.run.base import ExperimentRuntime
from app.run.base import ExperimentResources
from .step import Step


class TimeDeltaStep(Step):
    def __init__(self, host: Host):
        super().__init__("time delta")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host
        self._time_delta_path = None

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources):
        self._time_delta_path = resources.resources_path() / "dut_time_delta.txt"

    def execute(self, runtime: ExperimentRuntime):
        offset_delta = self._get_ntp_delta()

        microseconds = offset_delta / datetime.timedelta(microseconds=1)
        status = "behind" if microseconds < 0 else "ahead"
        delta_str = humanize.precisedelta(offset_delta, minimum_unit="microseconds")
        self._logger.info("Host %s is %s %s", self._host.host, status, delta_str)

        with self._time_delta_path.open(mode="w", encoding="utf-8") as f:
            iso_str = isodate.duration_isoformat(offset_delta)
            f.write(f'delta = "{iso_str}"')

    def _get_ntp_delta(self):
        ntp_client = ntplib.NTPClient()
        self._logger.debug("get time diff to: %s", self._host.host)
        response = ntp_client.request(self._host.host, version=4)  # v4 is common
        offset_delta = datetime.timedelta(seconds=response.offset)
        return offset_delta
