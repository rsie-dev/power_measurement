from pyinfra.operations import apt, files
from pyinfra.api import deploy


@deploy("NetworkBase")
def base_network():
    apt.packages(
        name="Install core network tools",
        packages=["iputils-ping", "iptables", "netcat-openbsd"],
        no_recommends=True,
        _sudo=True,
    )

    apt.packages(
        name="Install wifi tools",
        packages=["wireless-tools", "wavemon"],
        no_recommends=True,
        _sudo=True,
    )


@deploy("Router")
def router():
    ntp_server()
    dhcp_server()


def ntp_server():
    _ntp_service()


def ntp_client():
    _ntp_service()

    files.line(
        name="Disable default debian NTP pool",
        path="/etc/chrony/chrony.conf",
        line="pool 2.debian.pool.ntp.org iburst",
        replace="#pool 2.debian.pool.ntp.org iburst",
        _sudo=True,
    )


def _ntp_service():
    apt.packages(
        name="Install NTP service",
        packages=["chrony"],
        _sudo=True,
    )


def dhcp_server():
    apt.packages(
        name="Install DHCP server",
        packages=["isc-dhcp-server"],
        no_recommends=True,
        _sudo=True,
    )

    # ToDo configure
    # ToDo use own IP addresses for router and ntp
    # option domain-name "swamp.de";
    # subnet 192.168.3.0 netmask 255.255.255.0 {
    #   range 192.168.3.200 192.168.3.220;
    #   option broadcast-address 192.168.3.255;
    #   option routers 192.168.3.1;
    #   option domain-name-servers 192.168.3.1;
    #   option ntp-servers    192.168.3.1;
    # }

    # ToDo take IP addresses from inventory
    # host raspi5_4 {
    #   #hardware ethernet 60:7d:09:01:f7:40;
    #   hardware ethernet 2c:cf:67:42:55:be;
    #   fixed-address 192.168.3.202;
    # }
    #
    # host radxax4 {
    #   hardware ethernet 10:02:b5:86:04:b7;
    #   fixed-address 192.168.3.203;
    # }
    #
    # host visionfive2 {
    #   hardware ethernet 6c:cf:39:00:85:3e;
    #   fixed-address 192.168.3.204;
    # }
    #
    # host visionfive2_lite {
    #   hardware ethernet 6c:cf:39:00:88:a6;
    #   fixed-address 192.168.3.205;
    # }