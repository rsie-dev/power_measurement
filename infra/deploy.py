from pyinfra.operations import apt
from pyinfra import host

from base import base
from telegraf import telegraf
from compressors import compressors
from system import switch_to_read_only, add_test_user


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
