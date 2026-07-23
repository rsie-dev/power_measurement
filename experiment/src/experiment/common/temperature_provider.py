from abc import ABC, abstractmethod


class TemperatureProvider(ABC):
    @abstractmethod
    def get_temp(self) -> float:
        pass
