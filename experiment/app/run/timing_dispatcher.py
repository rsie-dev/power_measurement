from app.experiment.log import TimingEntry, Logger


class TimingDispatcher(Logger[TimingEntry]):
    def __init__(self):
        self._loggers: list[Logger[TimingEntry]] = []

    def register_logger(self, logger: Logger[TimingEntry]):
        self._loggers.append(logger)

    def unregister_logger(self, logger: Logger[TimingEntry]):
        self._loggers.remove(logger)

    def log(self, data: TimingEntry) -> None:
        for logger in self._loggers:
            logger.log(data)
