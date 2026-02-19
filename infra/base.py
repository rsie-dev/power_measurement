from pyinfra.operations import apt, files, server
from pyinfra import host
from pyinfra.api import deploy


@deploy("Base")
def base():
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

    files.directory(
        name="Ensure apt last update time folder exists",
        path="/var/lib/apt/periodic",
        _sudo=True,
    )

    apt.update(
            name="Update apt repositories",
            cache_time=10 * 60,
            _sudo=True,
            )

    apt.packages(
        name="Install base packages",
        packages=["fish", "vim", "less", "tmux", "wget", "lm-sensors", "duf", "bat", "time"],
        no_recommends=True,
        _sudo=True,
    )

    apt.packages(
        name="Install fix for ssh disconnect",
        packages=["libpam-systemd", "dbus"],
        no_recommends=True,
        _sudo=True,
    )


@deploy("BaseFileSystem")
def base_filesystem():
    apt.packages(
        name="Install filesystem support",
        packages=["btrfs-progs", "xfsprogs"],
        no_recommends=True,
        _sudo=True,
    )