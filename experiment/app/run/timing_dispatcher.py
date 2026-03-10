from app.experiment.log import TimingEntry, TimingLogger


class TimingDispatcher(TimingLogger):
    def __init__(self):
        self._loggers: list[TimingLogger] = []

    def register_logger(self, logger: TimingLogger):
        self._loggers.append(logger)

    def unregister_logger(self, logger: TimingLogger):
        self._loggers.remove(logger)

    def log(self, data: TimingEntry) -> None:
        for logger in self._loggers:
            logger.log(data)
