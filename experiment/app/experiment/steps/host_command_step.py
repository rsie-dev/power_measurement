import logging
from typing import Optional
from io import BytesIO, TextIOWrapper
import csv
from abc import abstractmethod

from fabric import Connection

from app.api import Command
from .step import Step
from .log_provider import LogProvider
from .host import SSHHost
from .experiment_environment import ExperimentEnvironment
from .experiment_runtime import ExperimentRuntime
from .experiment_resources import ExperimentResources


class CommandExecutor(Command):
    def __init__(self, command: str, with_timing: bool = False, work_dir: Optional[str] = None):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._command: str = command
        self._with_timing = with_timing
        self._work_dir = work_dir

    def execute(self, connection: Connection, resources_path):
        command = self._command
        timing_output = None
        exec_info = ""
        if self._with_timing:
            exec_info = " [timed]"
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
                timing_entries = self._extract_timing_entries(time_info)
                timings = " ".join(f"{key}: {value}" for key, value in timing_entries.items())
                self._logger.info("execution times: %s", timings)
                self._write_timing_entries(resources_path, timing_entries)

    def _write_timing_entries(self, resources_path, timing_entries):
        field_names = ["entry", "time_S"]
        with resources_path.open(mode="w", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=field_names)
            writer.writeheader()
            for key, value in timing_entries.items():
                writer.writerow({"entry": key, "time_S": value})

    def _extract_timing_entries(self, time_file: BytesIO) -> dict[str, float]:
        entries = {}
        time_file.seek(0)
        with TextIOWrapper(time_file, encoding="utf-8") as text_stream:
            for line in text_stream:
                key, value = line.strip().split(maxsplit=1)
                entries[key] = float(value)
        return entries


class BaseHostCommandStep(Step):
    def __init__(self, name: str, host: SSHHost):
        super().__init__(name)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources):
        environment.register_ssh_connection(self._host.ssh_user, self._host.host)

    @abstractmethod
    def _execute_commands(self, connection: Connection) -> None:
        pass

    def execute(self, runtime: ExperimentRuntime):
        connection = runtime.get_ssh_connection(self._host.ssh_user, self._host.host)
        self._execute_commands(connection)


class HostCommandStep(BaseHostCommandStep):
    def __init__(self, host: SSHHost, runs: int, commands: list[Command], log_providers: list[LogProvider]):
        super().__init__("host command", host)
        self._logger = logging.getLogger(self.__class__.__name__)
        self._runs = runs
        self._commands: list[Command] = commands
        self._log_providers = log_providers
        self._resources_path = None

    def prepare(self, environment: ExperimentEnvironment, resources: ExperimentResources):
        super().prepare(environment, resources)
        self._resources_path = resources.resources_path()

    def _execute_commands(self, connection: Connection):
        self._logger.info("on host: %s execute %d command(s)", self._host.host, len(self._commands))

        resources_path = self._resources_path / self._host.host_name
        resources_path.mkdir(parents=True, exist_ok=True)

        for run in range(self._runs):
            self._logger.info("Start run %d/%d", run + 1, self._runs)
            run_resources_path = resources_path / ("run_%03d" % (run + 1))
            run_resources_path.mkdir(parents=True, exist_ok=True)

            for log_provider in self._log_providers:
                log_provider.start_log(run_resources_path)

            timings_resources_path = run_resources_path / "timings.csv"
            for command in self._commands:
                command.execute(connection, timings_resources_path)

            for log_provider in self._log_providers:
                log_provider.stop_log()

        self._logger.info("commands executed")
