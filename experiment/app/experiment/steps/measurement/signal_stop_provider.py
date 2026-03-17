from usb_multimeter import StopProvider

from app.common import ShutdownHandler


class SignalStopProvider(StopProvider, ShutdownHandler):
    def __init__(self):
        self._should_stop = False

    def shut_down(self, _force: bool) -> None:
        self._should_stop = True

    def should_stop(self) -> bool:
        return self._should_stop
