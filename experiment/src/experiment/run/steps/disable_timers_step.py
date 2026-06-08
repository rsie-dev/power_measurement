import logging
from concurrent.futures import Executor
import json

from experiment.common import SSHHost
from experiment.run.base import ExperimentEnvironment
from experiment.run.base import ExperimentRuntime
from experiment.run.base import ExperimentResources

from .step import Step


class DisableTimersStep(Step):
    TIMER_FILE = "/tmp/active_timers.json"

    def __init__(self, host: SSHHost):
        super().__init__("disable timers")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources) -> None:
        environment.register_ssh_connection(self._host.ssh_user, self._host.host)

    def start(self, runtime: ExperimentRuntime, executor: Executor) -> None:
        connection = runtime.get_ssh_connection(self._host.ssh_user, self._host.host)
        result = connection.run(f"test -f {self.TIMER_FILE}", warn=True, hide=True)
        if not result.ok:
            self._logger.debug("create a list of active timers")
            command = f"systemctl list-units --type=timer --state=active --output=json > {self.TIMER_FILE}"
            connection.run(command, hide=True)

        timer_units = self._load_timers(connection)
        self._timer_command(connection, "stop", timer_units)

    def stop(self, runtime: ExperimentRuntime) -> None:
        connection = runtime.get_ssh_connection(self._host.ssh_user, self._host.host)
        timer_units = self._load_timers(connection)
        self._timer_command(connection, "start", timer_units)

    def _timer_command(self, connection, op: str, timer_units: list[str]):
        units = " ".join(timer_units)
        self._logger.info("%s timers: %s", op[:1].upper() + op[1:], units)
        command = f"systemctl {op} {units}"
        connection.sudo(command, hide=True)

    def _load_timers(self, connection) -> list[str]:
        self._logger.debug("download list of active timers")
        result = connection.run(f"cat {self.TIMER_FILE}", hide=True)
        content = result.stdout
        timers = json.loads(content)
        timer_units = [e["unit"] for e in timers]
        return timer_units
