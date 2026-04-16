import crypt
from io import StringIO

from pyinfra.api import deploy
from pyinfra.operations import files
from pyinfra.operations import server


@deploy("Add users")
def add_users():
    pass


def add_user(user: str):
    hashed_pw = crypt.crypt(user, crypt.mksalt(crypt.METHOD_SHA512))
    server.user(
        name="Create test user",
        user=user,
        password=hashed_pw,
        shell="/bin/bash",
        create_home=True,
        _sudo=True,
    )

    lines = []
    for op in ["status","start","stop","restart"]:
        lines.append(f"{user} ALL=(ALL) NOPASSWD: /usr/bin/systemctl {op} telegraf@*.service")
    content = StringIO("\n".join(lines) + "\n")
    files.put(
        name="Allow %s to control telegraf service" % user,
        src=content,
        dest="/etc/sudoers.d/%s" % user,
        _sudo=True,
    )


