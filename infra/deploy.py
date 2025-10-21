import getpass
import io

from pyinfra.operations import apt, files, server
from pyinfra import host
from pyinfra.facts.server import Arch

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

def get_telegraf_arch():
    arch = host.get_fact(Arch, )
    if arch == "aarch64":
        return "arm64"
    return arch

telegraf_version="1.36.3-1"
telegraf_package="telegraf_%s_%s.deb" % (telegraf_version, get_telegraf_arch())
files.download(
    name="Download telgraf package",
    src="https://dl.influxdata.com/telegraf/releases/%s" % telegraf_package,
    dest="/var/tmp/%s" % telegraf_package,
)
apt.deb(
    name="Install telegraf",
    src="/var/tmp/%s" % telegraf_package,
    _sudo=True,
)
