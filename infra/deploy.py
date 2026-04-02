from pyinfra.operations import apt, server
from pyinfra import host

from base import base, base_filesystem
from develop import develop
from network import base_network, router, ntp_client
from telegraf import telegraf
from compressors import compressors, stressors
from system import switch_to_read_only, add_test_user, unify_memory_size
from ssh import install_ssh_keys


server.mount(
    name="Ensure / is mounted RW",
    path="/",
    options=["remount", "rw"],
    _sudo=True,
)

base()
base_network()

if "controller" in host.groups:
    develop()
    router()
    base_filesystem()


if "dut" in host.groups:
    if host.data.get("install_cpupower", True):
        apt.packages(
            name="Install CPU power util",
            packages=["linux-cpupower"],
            no_recommends=True,
            _sudo=True,
        )

    ntp_client()
    telegraf()
    stressors()
    compressors()
    test_user = "ctest"
    add_test_user(test_user)
    install_ssh_keys(test_user)
    unify_memory_size()


switch_to_read_only()
