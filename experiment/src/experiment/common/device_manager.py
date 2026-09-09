from abc import ABC, abstractmethod

from usb_multimeter.device import Device


class DeviceManager(ABC):
    @abstractmethod
    def get_device(self) -> Device:
        pass

    @property
    @abstractmethod
    def serial_number(self) -> str:
        pass
