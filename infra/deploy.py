from pyinfra.operations import apt, files, server
from pyinfra import host

from telegraf import telegraf


server.hostname(
        name="Set hostname",
        hostname=host.name,
        _sudo=True,
        )

files.file(
    name="Remove check password trigger file",
    path="/var/lib/dietpi/.check_user_passwords",
    present=False,
    _sudo=True,
)

apt.update(
        name="Update apt repositories",
        _sudo=True,
        )

apt.packages(
    name="Install base packages",
    packages=["fish", "vim", "less", "tmux", "iputils-ping", "iptables", "wget", "git", "lm-sensors"],
    no_recommends=True,
    _sudo=True,
)

if host.data.get("install_cpupower", True):
    apt.packages(
        name="Install CPU power util",
        packages=["linux-cpupower"],
        no_recommends=True,
        _sudo=True,
    )

apt.packages(
    name="Install fix for ssh disconnect",
    packages=["libpam-systemd", "dbus"],
    no_recommends=True,
    _sudo=True,
)


apt.packages(
    name="Install network tools",
    packages=["wireless-tools", "netcat-openbsd", "wavemon"],
    no_recommends=True,
    _sudo=True,
)

apt.packages(
    name="Install compression tools",
    packages=["xz-utils", "lzop", "lz4", "bzip2", "bzip3"],
    no_recommends=True,
    _sudo=True,
)

apt.packages(
    name="Install stressor tools",
    packages=["stress-ng"],
    no_recommends=True,
    _sudo=True,
)

apt.packages(
    name="Install python",
    packages=["python3", "python3-venv"],
    no_recommends=True,
    _sudo=True,
)


telegraf()
