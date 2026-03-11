import logging

from app.usb_meter import devices_by_serial_number
from app.usb_meter.device import Device


class MultimeterDeviceManager:
    def __init__(self, serial_number: str):
        self._logger = logging.getLogger(self.__class__.__name__)
        self._serial_number = serial_number
        self._device = None

    def get_device(self) -> Device:
        if not self._device:
            device = self._find_device()
            self._logger.info("Multimeter with serial number %s is an %s %s model %s", self._serial_number,
                              device.manufacturer_name, device.product_name, device.device_info.model.name)
            self._device = device
        return self._device

    def _find_device(self) -> Device:
        devices = devices_by_serial_number(self._serial_number)
        device = next(devices, None)
        if not device:
            raise RuntimeError("No devices found with: %s" % self._serial_number)
        if next(devices, None):
            raise RuntimeError("Too many devices found with: %s" % self._serial_number)
        return device
