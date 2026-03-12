import logging
import json
from io import StringIO

import dotenv

from app.common import SSHHost
from app.experiment.base import ExperimentRuntime
from .hostname_validation_step import HostnameValidationStep


class HostnameInfoStep(HostnameValidationStep):
    def __init__(self, host: SSHHost):
        super().__init__(host)
        self._name = "host information"
        self._logger = logging.getLogger(self.__class__.__name__)

    def execute(self, runtime: ExperimentRuntime) -> None:
        connection = runtime.get_ssh_connection(self._host.ssh_user, self._host.host)
        self._logger.info("Hostname: %s", self._host.host_name)
        self._logger.info("IP:       %s", self._host.host)
        self._report_cpu_info(connection)
        self._report_os_info(connection)

    def _report_cpu_info(self, connection):
        result = connection.run('/usr/bin/lscpu -J', hide=True)
        cpu_info = json.loads(result.stdout)
        architecture = self._get_data(cpu_info, "Architecture:")
        model_name = self._get_data(cpu_info, "Model name:")
        model = self._get_data(cpu_info, "Model:")
        cpu_count = int(self._get_data(cpu_info, "CPU(s):"))
        vendor_id = self._get_data(cpu_info, "Vendor ID:")
        self._logger.info("CPU:      %d %s %s (%s) %s", cpu_count, vendor_id, model_name, model, architecture)

    def _get_data(self, cpu_info, field):
        for entry in cpu_info["lscpu"]:
            if entry["field"].lower() == field.lower():
                return entry["data"]
        return "n/a"

    def _report_os_info(self, connection):
        result = connection.run('cat /etc/os-release', hide=True)
        release_info = dotenv.dotenv_values(stream=StringIO(result.stdout))
        self._logger.info("OS:       %s %s", release_info["NAME"], release_info["DEBIAN_VERSION_FULL"])
