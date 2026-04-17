from pyinfra.operations import apt, files, server
from pyinfra.api import deploy


@deploy("Develop")
def develop():
    apt.packages(
        name="Install SCM tools",
        packages=["git", "subversion"],
        no_recommends=True,
        _sudo=True,
    )
    apt.packages(
        name="Install python",
        packages=["python3", "python3-venv", "python3-pip", "python3-socks"],
        no_recommends=True,
        _sudo=True,
    )
    apt.packages(
        name="Install monitoring tools",
        packages=["htop", "btop", "iotop", "sysstat"],
        no_recommends=True,
        _sudo=True,
    )

    synced = files.sync(
        name="Sync udev rules",
        src="udev/",
        dest="/etc/udev/rules.d/",
        _sudo=True,
    )

    server.shell(
        name="Update udev rules",
        commands=["udevadm control --reload-rules", "udevadm trigger"],
        _sudo=True,
        _if=synced.did_change,
    )