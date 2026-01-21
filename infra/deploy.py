from pyinfra.operations import apt, server
from pyinfra import host

from base import base
from telegraf import telegraf
from compressors import compressors
from system import switch_to_read_only, add_test_user


server.mount(
    name="Ensure / is mounted RW",
    path="/",
    options=["remount", "rw"],
    _sudo=True,
)

base()

if host.data.get("install_cpupower", True):
    apt.packages(
        name="Install CPU power util",
        packages=["linux-cpupower"],
        no_recommends=True,
        _sudo=True,
    )

telegraf()
compressors()
switch_to_read_only()

add_test_user()
