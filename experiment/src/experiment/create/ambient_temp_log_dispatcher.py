import logging

from usb_multimeter import ElectricalMeasurement

from experiment.run.log import Logger
from experiment.run.log import LogDispatcher
from experiment.run.log import TemperatureEntry


class AmbientTempLogDispatcher(LogDispatcher[TemperatureEntry], Logger[ElectricalMeasurement]):
    def __init__(self, latest_only: bool = False):
        super().__init__()
        self._logger = logging.getLogger(self.__class__.__name__)
        self._latest_only = latest_only

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
        super().log(te)
