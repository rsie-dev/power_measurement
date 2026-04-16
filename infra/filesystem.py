import json
from pathlib import Path

from pyinfra import logger
from pyinfra import host
from pyinfra.api import FactBase
from pyinfra.api import operation
from pyinfra.api import StringCommand

from filesystem_entry import FilesystemEntry


class Filesystem(FactBase):
    def __init__(self):
        super().__init__()
        self._device = None
        self._part_number = None

    def command(self, device: str, part_number: int):
        self._device = device
        self._part_number = part_number
        return f"sudo lsblk -J {device} -o NAME,FSTYPE"

    def process(self, output):
        content = json.loads("\n".join(output))
        devices = content["blockdevices"]
        target_device_path = Path(self._device)
        part_device = Path(f"{self._device}p{self._part_number}")
        for device_entry in devices:
            device = device_entry["name"]
            if device == target_device_path.stem:
                for child in device_entry["children"]:
                    if child["name"] == part_device.stem:
                        entry = FilesystemEntry(
                            name=part_device,
                            fs_type=child["fstype"],
                        )
                        return entry
        return None


@operation()
def format_partition(device: str, part_number: int):
    filesystem = host.get_fact(Filesystem, device, part_number)
    if filesystem.fs_type is not None:
        host.noop("partition {0} already contains filesystem: {1}".format(filesystem.name, filesystem.fs_type))
        return

    part_device = Path(f"{device}p{part_number}")
    logger.info("Format partition: {0}".format(part_device))
    yield StringCommand("/sbin/mkfs.xfs", part_device)
