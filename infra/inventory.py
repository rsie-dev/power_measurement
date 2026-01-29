import getpass

user_name = "dietpi"
PASSWORD = getpass.getpass(prompt="password for %s: " % user_name)

SERVER_IP = "192.168.1.203"
SERVER_PORT = 10000

_ssh_config = {
    "ssh_user": user_name,
    "ssh_password": PASSWORD,
    "_sudo_password": PASSWORD,
    "server_ip": SERVER_IP,
    "server_port": SERVER_PORT,
}


controller = ([
        ('controller', {'ssh_hostname': '192.168.1.201'}),
        ],
        _ssh_config
)

dut = ([
        ('raspi5', {'ssh_hostname': '192.168.1.202'}),
        ('radxax4', {'ssh_hostname': '192.168.1.203'}),
        ('visionfive2', {'ssh_hostname': '192.168.1.204'}),
        ('visionfive2lite', {'ssh_hostname': '192.168.1.205', "install_cpupower": False}),
        ],
        _ssh_config
)

