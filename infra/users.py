import crypt
from io import StringIO
from pathlib import Path

from pyinfra import host
from pyinfra.api import deploy, operation
from pyinfra.operations import files, server
from pyinfra.facts.server import Users

from ssh import install_ssh_key, read_ssh_key


@deploy("Add users")
def add_users():
    users = _collect_user_names()
    for user, keyfile in users.items():
        add_user(
            name="Create user: %s" % user,
            user=user,
            _sudo=True,
        )
        key = read_ssh_key(keyfile)
        install_ssh_key(user, key)
        allow_user_power_control(user)
        files.put(
            name="Copy README file",
            src="README_develop.md",
            dest=f"/home/{user}/README.md",
            _sudo=True,
        )


def _collect_user_names():
    ssh_folder = Path.cwd() / "ssh_keys"
    users = {}
    for path in ssh_folder.glob("*.pub"):
        if path.is_file():
            user = path.stem.split('_', 1)[0]
            users[user.lower()] = path
    return users


@operation()
def add_user(user: str):
    users = host.get_fact(Users, )
    if user in users:
        host.noop("user {0} already exist".format(user))
        return

    hashed_pw = crypt.crypt(user, crypt.mksalt(crypt.METHOD_SHA512))
    yield from server.user._inner(
        user=user,
        password=hashed_pw,
        shell="/bin/bash",
        create_home=True,
    )


def allow_user_telegraf_control(user: str):
    lines = []
    for op in ["status", "start", "stop", "restart"]:
        lines.append(f"{user} ALL=(ALL) NOPASSWD: /usr/bin/systemctl {op} telegraf@*.service")
    content = StringIO("\n".join(lines) + "\n")
    files.put(
        name="Allow %s to control telegraf service" % user,
        src=content,
        dest="/etc/sudoers.d/%s_telegraf" % user,
        _sudo=True,
    )


def allow_user_power_control(user: str):
    content = f"""
{user} ALL=(root) /bin/systemctl reboot, /bin/systemctl poweroff
{user} ALL=(root) /sbin/reboot, /sbin/shutdown, /sbin/poweroff
"""
    files.put(
        name="Allow %s to shut down / reboot the machine" % user,
        src=StringIO(content),
        dest="/etc/sudoers.d/%s_power" % user,
        _sudo=True,
    )
