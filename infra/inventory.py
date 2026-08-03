import getpass

user_name = "dietpi"
PASSWORD = getpass.getpass(prompt="password for %s: " % user_name)

SERVER_IP = "192.168.1.203"
SERVER_PORT = 10000

_ssh_config = {
    "ssh_user": user_name,
    "ssh_password": PASSWORD,
    "_sudo_password": PASSWORD,
}

_proxy_config = {
    "use_proxy": True,
}


controller = ([
        ('controller', {'ssh_hostname': '192.168.5.1'}),
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
