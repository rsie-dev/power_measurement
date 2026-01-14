from pathlib import Path

from pyinfra import host
from pyinfra.api import deploy
from pyinfra.operations import files
from pyinfra.facts.files import Link


@deploy("Switch to read only")
def switch_to_read_only():
    set_kernel_ro_flag()
    # ToDo:
    #update_fstab()


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
