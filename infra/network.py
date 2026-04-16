from ipaddress import IPv4Address, ip_address, IPv4Network

from pyinfra.operations import apt, files
from pyinfra.api import deploy
from pyinfra import inventory


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
    ip = ip_address("192.168.5.1")
    set_static_ip(ip)
    dhcp_server(ip)


def set_static_ip(ip: IPv4Address):
    # fixme
    pass


def dhcp_server(ip: IPv4Address):
    apt.packages(
        name="Install DHCP server",
        packages=["isc-dhcp-server"],
        no_recommends=True,
        _sudo=True,
    )

    dhcp_conf = "/etc/dhcp/dhcpd.conf"

    files.line(
        name="Set DHCP domain name",
        path=dhcp_conf,
        line='option domain-name "example.org";',
        replace='option domain-name "comptest.org";',
        _sudo=True,
    )
    #files.line(
    #    name="Set DHCP authorative",
    #    path=dhcp_conf,
    #    line='#authoritative;',
    #    replace='authoritative;',
    #    _sudo=True,
    #)
    files.line(
        name="Disable DHCP DNS server addresses",
        path=dhcp_conf,
        line='option domain-name-servers ns1.example.org, ns2.example.org;',
        replace='#option domain-name-servers ns1.example.org, ns2.example.org;',
        _sudo=True,
    )

    n = IPv4Network(ip).supernet(new_prefix=24)
    subnet_def = f"""
subnet {n.network_address} netmask {n.netmask} {{
  range {n.network_address + 200} {n.network_address + 220};
  option broadcast-address {n.broadcast_address};
  option routers {ip};
  option ntp-servers {ip};
}}

"""
    host_entries = []
    for host in inventory.get_group('dut'):
        entry = f"""
host {host.name} {{
  hardware ethernet {host.data.MAC};
  fixed-address {host.data.ssh_hostname};
}}
"""
        host_entries.append(entry)

    files.block(
        name="Add DHCP subnet",
        path=dhcp_conf,
        content=subnet_def + "\n".join(host_entries),
        before=True,
        line='# This is a very basic subnet declaration.',
        _sudo=True,
    )
