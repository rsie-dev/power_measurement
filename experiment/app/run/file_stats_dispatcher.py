from app.experiment.log import FileStatsEntry, Logger


class FileStatsDispatcher(Logger[FileStatsEntry]):
    def __init__(self):
        self._loggers: list[Logger[FileStatsEntry]] = []

    def register_logger(self, logger: Logger[FileStatsEntry]):
        self._loggers.append(logger)

    def unregister_logger(self, logger: Logger[FileStatsEntry]):
        self._loggers.remove(logger)

    def log(self, data: FileStatsEntry) -> None:
        for logger in self._loggers:
            logger.log(data)
