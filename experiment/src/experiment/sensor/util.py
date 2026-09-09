from typing import Generator
from glob import glob

from digitemp.master import UART_Adapter
from digitemp.device import TemperatureSensor

from .sensor_device import SensorModel, SensorDevice, DeviceInfo


def _build_device(adapter: UART_Adapter, rom: str | None = None):
    sensor = TemperatureSensor(adapter, rom=rom)
    if rom is None:
        rom = sensor.rom
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
