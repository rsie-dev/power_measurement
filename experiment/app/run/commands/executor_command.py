import logging
from typing import Optional
from io import BytesIO, TextIOWrapper
import csv

from fabric import Connection

from app.api import Command


class ExecutorCommand(Command):
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
