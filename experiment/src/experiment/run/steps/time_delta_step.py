import logging
import datetime as dt

import ntplib
import humanize
import isodate

from experiment.common import Host
from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentRuntime
from experiment.run.base import ExperimentResources
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
        offset_delta, destination, local, remote = self._get_ntp_delta()

        precision = "microseconds"
        local_time = local.astimezone()
        local_time_str = local_time.isoformat(timespec=precision)

        remote_time = remote.astimezone()
        remote_time_str = remote_time.isoformat(timespec=precision)

        self._logger.info("Time local:  %s", local_time_str)
        self._logger.info("Time device: %s", remote_time_str)

        microseconds = offset_delta / dt.timedelta(microseconds=1)
        status = "behind" if microseconds < 0 else "ahead"
        delta_str = humanize.precisedelta(offset_delta, minimum_unit=precision)
        self._logger.info("%s is %s %s", self._host.host_name, status, delta_str)

        with self._time_delta_path.open(mode="w", encoding="utf-8") as f:
            iso_str = isodate.duration_isoformat(offset_delta)
            f.write(f'delta = "{iso_str}"')

    def _get_ntp_delta(self) -> tuple[dt.timedelta, dt.datetime, dt.datetime, dt.datetime]:
        ntp_client = ntplib.NTPClient()
        self._logger.debug("get time diff to: %s", self._host.host)
        response = ntp_client.request(self._host.host, version=4)  # v4 is common
        offset_delta = dt.timedelta(seconds=response.offset)
        destination = dt.datetime.fromtimestamp(response.tx_time, tz=dt.timezone.utc)
        local = dt.datetime.fromtimestamp(response.dest_time, tz=dt.timezone.utc)
        remote = dt.datetime.fromtimestamp(response.dest_time + response.offset, tz=dt.timezone.utc)
        return offset_delta, destination, local, remote
