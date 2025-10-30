import sys
import signal
import logging
import contextlib
import threading
from collections.abc import Generator
from types import FrameType

from system_meter import ShutdownHandler

HANDLED_SIGNALS = (
    signal.SIGINT,  # Unix signal 2. Sent by Ctrl+C.
    signal.SIGTERM,  # Unix signal 15. Sent by `kill <pid>`.
)
if sys.platform == "win32":  # pragma: py-not-win32
    HANDLED_SIGNALS += (signal.SIGBREAK,)  # Windows signal 21. Sent by Ctrl+Break.


class SignalHandler:
    def __init__(self):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._captured_signals: list[int] = []
        self._shutdown_handlers: list[ShutdownHandler] = []
        self._should_exit = False

    def add_shutdown_handler(self, handler: ShutdownHandler):
        self._shutdown_handlers.append(handler)

    def _handle_exit(self, sig: int, _frame: FrameType | None) -> None:
        self._logger.info("caught signal: %s (%d)", signal.Signals(sig).name, sig)
        self._captured_signals.append(sig)
        force_exit = False
        if self._should_exit and sig == signal.SIGINT:
            force_exit = True  # pragma: full coverage
        else:
            self._should_exit = True
        handlers = self._shutdown_handlers[:]
        for handler in handlers:
            handler.shut_down(force_exit)

    @contextlib.contextmanager
    def capture_signals(self) -> Generator[None, None, None]:
        # Signals can only be listened to from the main thread.
        if threading.current_thread() is not threading.main_thread():
            yield
            return
        # always use signal.signal, even if loop.add_signal_handler is available
        # this allows to restore previous signal handlers later on
        original_handlers = {sig: signal.signal(sig, self._handle_exit) for sig in HANDLED_SIGNALS}
        try:
            yield
        finally:
            for sig, handler in original_handlers.items():
                signal.signal(sig, handler)
        # If we did gracefully shut down due to a signal, try to
        # trigger the expected behaviour now; multiple signals would be
        # done LIFO, see https://stackoverflow.com/questions/48434964
        for captured_signal in reversed(self._captured_signals):
            signal.raise_signal(captured_signal)
