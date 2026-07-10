import logging
from threading import Event, Condition

from fabric import Connection

from experiment.common import SSHHost
from experiment.ssh import SSHManager
from experiment.run.log import LogDispatcher


class SBCTemperatureCollector:
    def __init__(self, host: SSHHost, ssh_manager: SSHManager):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._host = host
        self._ssh_manager = ssh_manager
        self._condition = Condition()
        self._stop = False
        self._update_interval = 1

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._logger.debug("Signal SBC temperature collector to shutdown")
        with self._condition:
            self._stop = True
            self._condition.notify()

    def run(self, measurement_dispatcher: LogDispatcher, event: Event) -> None:
        self._logger.debug("SBC temperature collector start")
        try:
            event.set()
            self._ssh_manager.register_ssh_connection(self._host.ssh_user, self._host.host)
            while True:
                with self._condition:
                    while not self._stop:
                        if not self._condition.wait(timeout=self._update_interval):
                            connection = self._ssh_manager.get_ssh_connection(self._host.ssh_user, self._host.host)
                            self._collect_temperature(connection)

                    if self._stop:
                        break
        finally:
            self._logger.debug("SBC temperature collector shut down")

    def _collect_temperature(self, connection: Connection):
        self._logger.warning("collecting SBC temp")
        result = connection.run('uname -s')
        self._logger.warning("got: %s", result.stdout.strip())
