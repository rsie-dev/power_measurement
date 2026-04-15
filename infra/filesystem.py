import json
from pathlib import Path
import re

from pyinfra import logger
from pyinfra import host
from pyinfra.api import FactBase
from pyinfra.api import operation
from pyinfra.api import StringCommand

from filesystem_entry import FilesystemEntry
from partition_entry import PartitionEntry


class Filesystem(FactBase):
    def __init__(self):
        super().__init__()
        self._partition = None

    def command(self, partition: PartitionEntry):
        self._partition = partition
        device_path = self._get_device_path()
        return f"sudo lsblk -J {device_path} -o NAME,FSTYPE"

    def process(self, output):
        content = json.loads("\n".join(output))
        devices = content["blockdevices"]
        target_device_path = self._get_device_path()
        for device_entry in devices:
            device = device_entry["name"]
            if device == target_device_path.stem:
                for child in device_entry["children"]:
                    if child["name"] == self._partition.node.stem:
                        entry = FilesystemEntry(
                            name=self._partition.node,
                            fs_type=child["fstype"],
                        )
                        return entry
        return None

    def _get_device_path(self):
        device = re.sub(r"p\d+$", "", str(self._partition.node))
        return Path(device)


@operation()
def format_partition(partition: PartitionEntry):
    filesystem = host.get_fact(Filesystem, partition)
    if filesystem.fs_type is not None:
        host.noop("partition {0} already contains filesystem: {1}".format(filesystem.name, filesystem.fs_type))
        return

    logger.info("Format partition: {0}".format(partition.node))
    yield StringCommand("/sbin/mkfs.xfs", str(partition.node))
