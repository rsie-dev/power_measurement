from dataclasses import dataclass
from enum import IntEnum
from typing import Generator
from glob import glob

from digitemp.master import UART_Adapter
from digitemp.device import TemperatureSensor


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
        self._device_info = device_info
        self._sensor = sensor

    @property
    def device_info(self) -> DeviceInfo:
        return self._device_info


def all_sensor_devices() -> Generator[SensorDevice, None, None]:
    serial_devices = sorted(glob("/dev/ttyUSB*"))
    for serial_device in serial_devices:
        adapter = UART_Adapter(serial_device)
        for rom in adapter.get_connected_ROMs():
            sensor = TemperatureSensor(adapter, rom=rom)
            family_code = sensor.FAMILY_CODE
            model = SensorModel(family_code)
            name = sensor._device_name(family_code) #  pylint: disable=protected-access
            name = name.partition(" - ")[2]
            info = DeviceInfo(
                bus=adapter.name,
                rom_code=rom,
                model=model,
                name=name,
            )
            device = SensorDevice(info, sensor)
            yield device
