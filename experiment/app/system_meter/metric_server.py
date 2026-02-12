import logging
import contextlib
from collections.abc import Generator
from types import FrameType
from typing import Callable

from uvicorn.config import Config
from uvicorn.server import Server

from app.common.shutdown_handler import ShutdownHandler
from .app import create_app
from .measurement_logger import MeasurementLogger


class NoSignalServer(Server, ShutdownHandler):
    @contextlib.contextmanager
    def capture_signals(self) -> Generator[None, None, None]:
        yield

    def handle_exit(self, sig: int, frame: FrameType | None) -> None:
        self.should_exit = True

    def shut_down(self, force: bool) -> None:
        if force:
            self.force_exit = True
        else:
            self.should_exit = True


class MetricsServer(ShutdownHandler):
    def __init__(self, metrics_server_address: tuple[str, int]):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._server = None
        self._metrics_server_address = metrics_server_address

    def shut_down(self, force: bool) -> None:
        if self._server is None:
            return
        self._server.shut_down(force)

    def run(self, measurement_logger: MeasurementLogger, startup_call_back: Callable) -> None:
        app = create_app(measurement_logger, startup_call_back)
        config = Config(
            app,
            host=self._metrics_server_address[0],
            port=self._metrics_server_address[1],
            log_config=None,
            log_level=None,
        )
        self._server = NoSignalServer(config=config)
        self._server.run()
