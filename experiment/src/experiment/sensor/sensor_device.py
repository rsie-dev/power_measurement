import logging
from dataclasses import dataclass
from enum import IntEnum
from typing import Generator
from glob import glob

from digitemp.master import UART_Adapter
from digitemp.device import TemperatureSensor
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
        self._logger.info("open sensor device: %s", self._device_info.bus)
        # Allows 5 Hz
        self._sensor.set_resolution(DS18B20.RES_10_BIT)

    def close(self) -> None:
        self._logger.info("close sensor device: %s", self._device_info.bus)
        self._sensor.bus.close()

    def get_temperature(self) -> float:
        if not self._sensor.bus.uart.is_open:
            raise RuntimeError("sensor on %s not opened" % self._device_info.bus)
        return self._sensor.get_temperature()


def _build_device(adapter: UART_Adapter, rom: str | None = None):
    sensor = TemperatureSensor(adapter, rom=rom)
    family_code = sensor.FAMILY_CODE
    model = SensorModel(family_code)
    name = sensor._device_name(family_code)  # pylint: disable=protected-access
    name = name.partition(" - ")[2]
    info = DeviceInfo(
        bus=adapter.name,
        rom_code=rom,
        model=model,
        name=name,
    )
    device = SensorDevice(info, sensor)
    return device


def all_sensor_devices() -> Generator[SensorDevice, None, None]:
    serial_devices = sorted(glob("/dev/ttyUSB*"))
    for serial_device in serial_devices:
        adapter = UART_Adapter(serial_device)
        for rom in adapter.get_connected_ROMs():
            device = _build_device(adapter, rom)
            yield device


def get_sensor_device(serial_device: str) -> SensorDevice:
    adapter = UART_Adapter(serial_device)
    device = _build_device(adapter)
    return device
