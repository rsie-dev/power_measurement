from pathlib import Path
import crypt
from io import StringIO


from pyinfra import host
from pyinfra.api import deploy
from pyinfra.operations import files
from pyinfra.operations import server
from pyinfra.facts.files import Link

from fstab import FstabDirs
from fstab import fstab_option,fstab_add_entry


@deploy("Switch to read only")
def switch_to_read_only():
    set_kernel_ro_flag()
    #update_fstab_ro()
    fix_dhcp_on_ro()


def fix_dhcp_on_ro():
    fstab_add_entry(
        device="tmpfs",
        mount_dir="/var/lib/dhcp",
        fs_type="tmpfs",
        fstab="/tmp/fstab",
    )


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


def add_test_user():
    test_user = "ctest"
    hashed_pw = crypt.crypt("ctest", crypt.mksalt(crypt.METHOD_SHA512))
    server.user(
        name="Create test user",
        user=test_user,
        password=hashed_pw,
        shell="/bin/bash",
        create_home=True,
        _sudo=True,
    )

    lines = []
    for op in ["status","start","stop","restart"]:
        lines.append(f"{test_user} ALL=(ALL) NOPASSWD: /usr/bin/systemctl {op} telegraf")
    content = StringIO("\n".join(lines) + "\n")
    files.put(
        name="Allow %s to control telegraf service" % test_user,
        src=content,
        dest="/etc/sudoers.d/%s" % test_user,
        _sudo=True,
    )
