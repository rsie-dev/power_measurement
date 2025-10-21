import getpass
import io

from pyinfra.operations import apt, files, server
from pyinfra import host

apt.update(
        name="Update apt repositories",
        _sudo=True,
        )

apt.packages(
    name="Install base packages",
    packages=["fish", "vim", "less", "tmux", "iputils-ping", "iptables", "wget", "git", "lm-sensors", "linux-cpupower"],
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
    name="Install python",
    packages=["python3", "python3-venv"],
    no_recommends=True,
    _sudo=True,
)
