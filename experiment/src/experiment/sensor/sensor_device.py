import logging
from dataclasses import dataclass
from enum import IntEnum

from digitemp.device import DS18B20


class SensorModel(IntEnum):
    DS2401 = 0x01
    DS18S20 = 0x10
    DS1822 = 0x22
    DS18B20 = 0x28


@dataclass(frozen=True)
class DeviceInfo:
    bus: str
    rom_code: str
    model: SensorModel
    name: str


class SensorDevice:
    def __init__(self, device_info: DeviceInfo, sensor):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._device_info = device_info
        self._sensor = sensor

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def open(self) -> None:
        self._logger.debug("open sensor device: %s", self._device_info.bus)
        # Allows up to 2 Hz
        self._sensor.set_resolution(DS18B20.RES_11_BIT)

    def close(self) -> None:
        self._logger.debug("close sensor device: %s", self._device_info.bus)
        self._sensor.bus.close()

    def get_temperature(self) -> float:
        if not self._sensor.bus.uart.is_open:
            raise RuntimeError("sensor on %s not opened" % self._device_info.bus)
        return self._sensor.get_temperature()
