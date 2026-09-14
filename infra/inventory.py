import getpass

user_name = "dietpi"
PASSWORD = getpass.getpass(prompt="password for %s: " % user_name)

_ssh_config = {
    "ssh_user": user_name,
    "ssh_password": PASSWORD,
    "_sudo_password": PASSWORD,
}

# On initial installation set to false with "--data use_proxy=False" and ensure the machine has internet connection.
# On subsequent / standalone installations leave it True and ensure a socks proxy is available
# by opening an ssh session prior to pyinfra with:
# ssh -R  9999 -l <user> <machine>
_proxy_config = {
    "use_proxy": True,
}

# On initial install, set the MAC address and IP address to the received IP address.
# On subsequent / standalone installation set to the default 192.168.5.<X>

controller = ([
        ('controller', {'ssh_hostname': '192.168.5.1', 'sync_data': False}),
        ],
        _ssh_config | _proxy_config
)

dut = ([
        ('raspi5', {'ssh_hostname': '192.168.5.102', "MAC": "2c:cf:67:42:55:be"}),
        ('radxax4', {'ssh_hostname': '192.168.5.103', "MAC": "10:02:b5:86:04:b7"}),
        ('visionfive2', {'ssh_hostname': '192.168.5.104', "MAC": "6c:cf:39:00:85:3e"}),
        ('visionfive2lite', {'ssh_hostname': '192.168.5.105', "MAC": "6c:cf:39:00:88:a6", "install_cpupower": False}),
        ('raspi1', {'ssh_hostname': '192.168.5.106', "MAC": "b8:27:eb:6a:76:b6"}),
       ],
        _ssh_config | _proxy_config
)
