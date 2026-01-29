from pyinfra.operations import apt
from pyinfra.api import deploy


@deploy("NetworkBase")
def network_base():
    apt.packages(
        name="Install core network tools",
        packages = ["iputils-ping", "iptables", "netcat-openbsd"],
        no_recommends = True,
        _sudo = True,
    )

    apt.packages(
        name="Install wifi tools",
        packages = ["wireless-tools", "wavemon"],
        no_recommends = True,
        _sudo = True,
    )
