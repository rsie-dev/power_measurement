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
    packages=["fish", "vim", "less", "tmux", "iputils-ping", "iptables", "wget", "git", "lm-sensors"],
    no_recommends=True,
    _sudo=True,
)

apt.packages(
    name="Install measurement packages",
    packages=["linux-cpupower"],
    no_recommends=True,
    _sudo=True,
)
