import json
from pathlib import Path

from pyinfra import logger
from pyinfra import host
from pyinfra.api import FactBase
from pyinfra.api import operation
from pyinfra.api import StringCommand

from partition_entry import PartitionEntry


class Partitions(FactBase):
    def command(self, device):
        return f"sudo /sbin/sfdisk -J {device}"

    def process(self, output):
        content = json.loads("\n".join(output))
        table = content["partitiontable"]
        entries = []
        for part_entry in table["partitions"]:
            bootable = part_entry["bootable"] if "bootable" in part_entry else False
            entry = PartitionEntry(
                node=Path(part_entry["node"]),
                start=part_entry["start"],
                size=part_entry["size"],
                type=part_entry["type"],
                bootable=bootable
            )
            entries.append(entry)
        return entries


class Partition(FactBase):
    def __init__(self):
        super().__init__()
        self._part_nr = None

    def command(self, device: str, part_nr: int):
        self._part_nr = part_nr
        return f"sudo /sbin/sfdisk -J {device}"

    def process(self, output):
        content = json.loads("\n".join(output))
        table = content["partitiontable"]
        for part_entry in table["partitions"]:
            node = part_entry["node"]
            if node.endswith(f"p{self._part_nr}"):
                bootable = part_entry["bootable"] if "bootable" in part_entry else False
                entry = PartitionEntry(
                    node=Path(part_entry["node"]),
                    start=part_entry["start"],
                    size=part_entry["size"],
                    type=part_entry["type"],
                    bootable=bootable
                )
                return entry
        return None


@operation()
def add_partition(device: str, part_number: int):
    partition = host.get_fact(Partition, device, part_number)
    if partition:
        host.noop("partition {1} on device {0} already exist".format(device, part_number))
        return

    logger.info("Add partition {1} to: {0}".format(device, part_number))
    cmd = f"echo ',+,83' | /sbin/sfdisk --force --no-reread --no-tell-kernel -N {part_number} {device}"
    yield StringCommand(cmd)

    logger.info("Re-read partition table")
    yield StringCommand("/sbin/partprobe", device)
