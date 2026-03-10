from app.experiment.log import FileStatsEntry, FileStatsLogger


class FileStatsDispatcher(FileStatsLogger):
    def __init__(self):
        self._loggers: list[FileStatsLogger] = []

    def register_logger(self, logger: FileStatsLogger):
        self._loggers.append(logger)

    def unregister_logger(self, logger: FileStatsLogger):
        self._loggers.remove(logger)

    def log(self, data: FileStatsEntry) -> None:
        for logger in self._loggers:
            logger.log(data)
