import logging
from typing import Optional
from io import BytesIO, TextIOWrapper

from fabric import Connection

from app.api import Command
from .step import Step
from .experiment_environment import ExperimentEnvironment
from .experiment_runtime import ExperimentRuntime
from .experiment_measurement import ExperimentMeasurement
from .experiment_resources import ExperimentResources


class CommandExecutor(Command):
    def __init__(self, command: str, with_timing: bool, work_dir: Optional[str] = None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._command: str = command
        self._with_timing = with_timing
        self._work_dir = work_dir

    def execute(self, connection: Connection):
        command = self._command
        timing_output = None
        exec_info = ""
        if self._with_timing:
            exec_info = " timed"
            result = connection.run("mktemp", hide=True)
            timing_output = result.stdout.strip()
            self._logger.debug("timing output: %s", timing_output)
            command = f"/usr/bin/time -p -o {timing_output} {self._command}"
        work_dir = self._work_dir if self._work_dir else "."
        self._logger.info("execute%s: %s", exec_info, self._command)
        with connection.cd(work_dir):
            connection.run(command, hide=True)
            if self._with_timing:
                time_info = BytesIO()
                connection.get(remote=timing_output, local=time_info)
                timing_infos = self._extract_timing_infos(time_info)
                self._logger.error("execution times: %s", timing_infos)

    def _extract_timing_infos(self, time_file: BytesIO) -> dict[str, float]:
        entries = {}
        time_file.seek(0)
        with TextIOWrapper(time_file, encoding="utf-8") as text_stream:
            for line in text_stream:
                key, value = line.strip().split(maxsplit=1)
                entries[key] = float(value)
        return entries


class HostCommandStep(Step):
    def __init__(self, host: str, ssh_user: str, commands: list[Command]):
        super().__init__("host command")
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host
        self._ssh_user = ssh_user
        self._commands: list[Command] = commands

    def prepare(self, environment: ExperimentEnvironment, measurement: ExperimentMeasurement,
                resources: ExperimentResources):
        environment.register_ssh_connection(self._ssh_user, self._host)

    def _execute_commands(self, connection: Connection):
        self._logger.info("on host: %s execute %d command(s)", self._host, len(self._commands))
        for command in self._commands:
            command.execute(connection)
        self._logger.info("commands executed")

    def execute(self, runtime: ExperimentRuntime):
        connection = runtime.get_ssh_connection(self._ssh_user, self._host)
        self._execute_commands(connection)
