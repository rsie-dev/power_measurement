from pathlib import Path
import crypt
from io import StringIO


from pyinfra import host
from pyinfra.api import deploy
from pyinfra.operations import files, systemd
from pyinfra.operations import server
from pyinfra.facts.files import Link
from pyinfra.facts.server import Arch

from fstab import FstabDirs
from fstab import fstab_option
from partition import Partitions, add_partition


@deploy("Switch to read only")
def switch_to_read_only():
    set_kernel_ro_flag()
    prepare_for_ro()
    update_fstab_ro()


def prepare_for_ro():
    var_lib_dhcp_mount = files.put(
        name="Create /var/lib/dhcp mount unit",
        src="var-lib-dhcp.mount",
        dest="/etc/systemd/system",
        _sudo=True,
    )
    tmp_dhcp_mount = files.put(
        name="Create /tmp/dhcp mount unit",
        src="tmp-dhcp.mount",
        dest="/etc/systemd/system",
        _sudo=True,
    )
    var_lib_dhcp_etc_mount = files.put(
        name="Create /var/lib/dhcp_etc mount unit",
        src="var-lib-dhcp_etc.mount",
        dest="/etc/systemd/system",
        _sudo=True,
    )
    var_tmp_dietpi_logs_mount = files.put(
        name="Create /var/tmp/dietpi/logs mount unit",
        src="var-tmp-dietpi-logs.mount",
        dest="/etc/systemd/system",
        _sudo=True,
    )

    new_resolv_folder = Path("/var/lib/dhcp_etc")
    files.directory(
        name="Alternative folder for resolv.conf",
        path=str(new_resolv_folder),
        _sudo=True,
    )
    etc_resolv = Path("/etc/resolv.conf")
    link_info = host.get_fact(Link, str(etc_resolv))
    if link_info is False:
        # Exists but not a link
        files.copy(
            name=f"Copy {etc_resolv} to overlay folder",
            src=str(etc_resolv),
            dest=str(new_resolv_folder),
            _sudo=True,
        )

    files.link(
        name=f"Create link {etc_resolv} that points to {new_resolv_folder / etc_resolv.name}",
        path=str(etc_resolv),
        target=str(new_resolv_folder / etc_resolv.name),
        force=True,
        _sudo=True,
    )

    if var_lib_dhcp_mount.changed or tmp_dhcp_mount.changed or var_lib_dhcp_etc_mount.changed or var_tmp_dietpi_logs_mount.changed:
        systemd.daemon_reload(
            name="Reload the systemd daemon",
            _sudo=True,
        )

    systemd.service(
        name="Enable the /var/lib/dhcp mount unit",
        service="var-lib-dhcp.mount",
        enabled=True,
        _sudo=True,
    )
    systemd.service(
        name="Enable the /var/lib/dhcp_etc mount unit",
        service="var-lib-dhcp_etc.mount",
        enabled=True,
        _sudo=True,
    )
    systemd.service(
        name="Enable the /var/tmp/dietpi/logs mount unit",
        service="var-tmp-dietpi-logs.mount",
        enabled=True,
        _sudo=True,
    )

    arch = host.get_fact(Arch, )
    adapt_fake_hwclock()
    disable_timers()

    if arch == "x86_64":
        prepare_for_ro_x86()


def adapt_fake_hwclock():
    tmp_fakehwclock_mount = files.put(
        name="Create /tmp/fakehwclock mount unit",
        src="tmp-fakehwclock.mount",
        dest="/etc/systemd/system",
        _sudo=True,
    )
    fakehwclock_override_conf = files.put(
        name="Create fake-hwclock-load override",
        src="fakehwclock_override.conf",
        dest="/etc/systemd/system/fake-hwclock-load.service.d/override.conf",
        _sudo=True,
    )
    if tmp_fakehwclock_mount.changed or fakehwclock_override_conf.changed:
        systemd.daemon_reload(
            name="Reload the systemd daemon",
            _sudo=True,
        )
    systemd.service(
        name="Enable the /tmp/fakehwclock mount unit",
        service="tmp-fakehwclock.mount",
        enabled=True,
        running=True,
        _sudo=True,
    )
    files.block(
        name="Set new location for fake-hwclock",
        path="/etc/default/fake-hwclock",
        content="FILE=/tmp/fakehwclock/fake-hwclock.data",
        after=True,
        line="#FORCE=false",
        _sudo=True,
    )


def disable_timers():
    systemd.service(
        name="Disable the dpkg-db-backup timer unit",
        service="dpkg-db-backup.timer",
        enabled=False,
        running=False,
        _sudo=True,
    )
    systemd.service(
        name="Disable the man-db timer unit",
        service="man-db.timer",
        enabled=False,
        running=False,
        _sudo=True,
    )


def prepare_for_ro_x86():
    grub_common_override = files.put(
        name="Add overlay for grub-common.service",
        src="grub-common_override.conf",
        dest="/etc/systemd/system/grub-common.service.d/override.conf",
        _sudo=True,
    )
    if grub_common_override.changed:
        systemd.daemon_reload(
            name="Reload the systemd daemon",
            _sudo=True,
        )


def update_fstab_ro():
    entries = ["/"]
    arch = host.get_fact(Arch, )
    if arch == "x86_64":
        entries.append("/boot/efi")
    elif arch == "riscv64":
        pass
    elif arch == "aarch64":
        entries.append("/boot/firmware")
    else:
        raise RuntimeError("unsupported architecture: %s" % arch)

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
    arch = host.get_fact(Arch, )
    if arch == "x86_64":
        set_kernel_ro_flag_x86()
    elif arch == "riscv64":
        set_kernel_ro_flag_riscv()
    elif arch == "aarch64":
        set_kernel_ro_flag_raspi()
    else:
        raise RuntimeError("unsupported architecture: %s" % arch)


def set_kernel_ro_flag_x86():
    grub = files.replace(
        name="Boot root FS ro",
        path="/etc/default/grub",
        text=r"GRUB_CMDLINE_LINUX=\"fsck.repair=yes net.ifnames=0\"",
        replace="GRUB_CMDLINE_LINUX=\"fsck.repair=yes net.ifnames=0 ro\"",
        _sudo=True,
    )
    if grub.changed:
        server.shell(
            name="Update grub",
            commands="/usr/sbin/update-grub",
            _sudo=True,
        )


def set_kernel_ro_flag_riscv():
    files.replace(
        name="Boot root FS ro",
        path="/boot/extlinux/extlinux.conf",
        text=r"rootfstype=ext4 rootwait",
        replace="rootfstype=ext4 ro rootwait",
        _sudo=True,
    )


def set_kernel_ro_flag_raspi():
    cmd_path = Path("/boot/firmware/cmdline.txt")
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


def add_user(user: str):
    hashed_pw = crypt.crypt(user, crypt.mksalt(crypt.METHOD_SHA512))
    server.user(
        name="Create test user",
        user=user,
        password=hashed_pw,
        shell="/bin/bash",
        create_home=True,
        _sudo=True,
    )

    lines = []
    for op in ["status","start","stop","restart"]:
        lines.append(f"{user} ALL=(ALL) NOPASSWD: /usr/bin/systemctl {op} telegraf@*.service")
    content = StringIO("\n".join(lines) + "\n")
    files.put(
        name="Allow %s to control telegraf service" % user,
        src=content,
        dest="/etc/sudoers.d/%s" % user,
        _sudo=True,
    )


def unify_memory_size():
    memory_limit_gb = 4
    arch = host.get_fact(Arch, )
    if arch == "x86_64":
        pass
    elif arch == "riscv64":
        _limit_kernel_memory(memory_limit_gb )
    elif arch == "aarch64":
        pass
    else:
        raise RuntimeError("unsupported architecture: %s" % arch)


def _limit_kernel_memory(memory_limit_gb: int):
    files.replace(
        name=f"Limit memory to {memory_limit_gb}GB",
        path="/boot/extlinux/extlinux.conf",
        text=r"rootwait earlycon",
        replace=f"rootwait mem={memory_limit_gb}G earlycon",
        _sudo=True,
    )


@deploy("Home partition")
def add_home_partition():
    device = "/dev/mmcblk0"
    add_partition(
        device=device,
        part_number=3,
        _sudo=True,
    )
