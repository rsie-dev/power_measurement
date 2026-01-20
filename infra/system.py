from pathlib import Path

from pyinfra import host
from pyinfra.api import deploy
from pyinfra.operations import files
from pyinfra.facts.files import Link

from fstab import FstabDirs
from fstab import fstab_option


@deploy("Switch to read only")
def switch_to_read_only():
    set_kernel_ro_flag()
    #update_fstab_ro()


def update_fstab_ro():
    entries = ["/", "/boot/firmware"]
    fstab_dirs = host.get_fact(FstabDirs)
    for entry in entries:
        if entry not in fstab_dirs:
            continue
        fstab_option(
            name="Change fstab entry ro: {0}".format(entry),
            mount_dir=entry,
            read_only=True,
            _sudo=True,
        )


def set_kernel_ro_flag():
    cmd_path = Path("/boot/cmdline.txt")
    link_info = host.get_fact(Link, str(cmd_path))
    if link_info:
        cmd_path = cmd_path.parent / link_info["link_target"]

    files.replace(
        name="Boot root FS ro",
        path=str(cmd_path),
        text=r"rootfstype=ext4 rootwait",
        replace="rootfstype=ext4 ro rootwait",
        _sudo=True,
    )
