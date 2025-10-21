import getpass
import io

from pyinfra.operations import apt, files, server
from pyinfra import host

apt.packages(
    name="Install base packages",
    packages=["fish", "vim", "less", "tmux", "iputils-ping", "iptables", "wget", "git", "cpufrequtils", "lm-sensors"],
    no_recommends=True,
    _sudo=True,
)

