from system_meter import ShutdownHandler
from usb_meter import StopProvider


class SignalStopProvider(StopProvider, ShutdownHandler):
    def __init__(self):
        self._should_stop = False

    def shut_down(self, _force: bool) -> None:
        self._should_stop = True

    def should_stop(self) -> bool:
        return self._should_stop
