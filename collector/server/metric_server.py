import logging
import contextlib
from collections.abc import Generator
from types import FrameType

from uvicorn.config import Config
from uvicorn.server import Server

from .shutdown_handler import ShutdownHandler
from .main import app


class NoSignalServer(Server, ShutdownHandler):
    def __init__(self, config: Config) -> None:
        super().__init__(config)

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
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._server = None

    def shut_down(self, force: bool) -> None:
        if self._server is None:
            return
        self._server.shut_down(force)

    def run(self, args) -> None:
        config = Config(
            app,
            host=args.host,
            port=args.port,
            log_config=None,
            log_level=None,
        )
        self._server = NoSignalServer(config=config)
        self._server.run()
