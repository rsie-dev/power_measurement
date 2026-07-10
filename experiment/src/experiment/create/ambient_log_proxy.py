import logging

from usb_multimeter import ElectricalMeasurement

from experiment.run.log import Logger, BaseLogger
from experiment.run.log import CSVAmbientTemperatureLogger, TemperatureEntry


class AmbientLogProxy(BaseLogger, Logger[ElectricalMeasurement]):
    def __init__(self, formatter: logging.Formatter, logger: CSVAmbientTemperatureLogger, latest_only: bool = False):
        super().__init__(formatter)
        self._logger = logger
        self._latest_only = latest_only

    def init(self) -> None:
        self._logger.init()

    def close(self) -> None:
        self._logger.close()

    def log(self, data: ElectricalMeasurement | list[ElectricalMeasurement]) -> None:
        if not isinstance(data, list):
            data = [data]
        if self._latest_only:
            self._log_measurement(data[-1])
        else:
            for measurement in data:
                self._log_measurement(measurement)

    def _log_measurement(self, data: ElectricalMeasurement) -> None:
        te = TemperatureEntry(
            timestamp=data.timestamp,
            temperature=data.temperature
        )
        self._logger.log(te)
