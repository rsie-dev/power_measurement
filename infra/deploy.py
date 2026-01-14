from pyinfra.operations import apt
from pyinfra import host

from base import base
from telegraf import telegraf
from compressors import compressors

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
