import crypt
from io import StringIO
from pathlib import Path

from pyinfra.api import deploy
from pyinfra.operations import files
from pyinfra.operations import server

from ssh import install_ssh_key, read_ssh_key


@deploy("Add users")
def add_users():
    users = _collect_user_names()
    for user, keyfile in users.items():
        add_user(user)
        key = read_ssh_key(keyfile)
        install_ssh_key(user, key)


def _collect_user_names():
    ssh_folder = Path.cwd() / "ssh_keys"
    users = {}
    for path in ssh_folder.glob("*.pub"):
        if path.is_file():
            user = path.stem.split('_', 1)[0]
            users[user] = path
    return users


def add_user(user: str):
    hashed_pw = crypt.crypt(user, crypt.mksalt(crypt.METHOD_SHA512))
    server.user(
        name="Create user: %s" % user,
        user=user,
        password=hashed_pw,
        shell="/bin/bash",
        create_home=True,
        _sudo=True,
    )


def allow_user_telegraf_control(user: str):
    lines = []
    for op in ["status", "start", "stop", "restart"]:
        lines.append(f"{user} ALL=(ALL) NOPASSWD: /usr/bin/systemctl {op} telegraf@*.service")
    content = StringIO("\n".join(lines) + "\n")
    files.put(
        name="Allow %s to control telegraf service" % user,
        src=content,
        dest="/etc/sudoers.d/%s" % user,
        _sudo=True,
    )
