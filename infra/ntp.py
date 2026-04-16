from io import StringIO

from pyinfra.api import deploy
from pyinfra.operations import apt, files, systemd


@deploy("NTP server")
def ntp_server():
    _ntp_service()
    config_file = _ntp_server_mode()
    systemd.service(
        name="Restart chrony service",
        service="chrony.service",
        restarted=True,
        _sudo=True,
        _if=config_file.did_change
    )


@deploy("NTP client")
def ntp_client():
    _ntp_service()
    config_file = _ntp_server_mode()

    update_config = files.line(
        name="Disable default debian NTP pool",
        path="/etc/chrony/chrony.conf",
        line="pool 2.debian.pool.ntp.org iburst",
        replace="#pool 2.debian.pool.ntp.org iburst",
        _sudo=True,
    )

    content = """
minsamples 8
maxsamples 64
maxupdateskew 20

hwtimestamp *

makestep 0.1 3
rtcsync
"""
    add_config = files.put(
        name="Create extra chrony client configuration",
        src=StringIO(content),
        dest="/etc/chrony/conf.d/client.conf",
        _sudo=True,
    )

    update_dhcp_config = files.line(
        name="Update DHCP chrony script",
        path="/etc/dhcp/dhclient-exit-hooks.d/chrony",
        line='echo "server $server iburst" >> "$SERVERFILE"',
        replace='echo "server $server iburst minpoll 2 maxpoll 4" >> "$SERVERFILE"',
        _sudo=True,
    )

    systemd.service(
        name="Restart chrony service",
        service="chrony.service",
        restarted=True,
        _sudo=True,
        _if=config_file.did_change or update_config.did_change() or add_config.did_change()
            or update_dhcp_config.did_change()
    )


def _ntp_service():
    apt.packages(
        name="Install NTP service",
        packages=["chrony"],
        _sudo=True,
    )


def _ntp_server_mode():
    config_file = files.put(
        name="Enable NTP server mode",
        src=StringIO("allow all"),
        dest="/etc/chrony/conf.d/server.conf",
        _sudo=True,
    )
    return config_file
