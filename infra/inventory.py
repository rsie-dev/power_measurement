import getpass

user_name = "dietpi"
PASSWORD = getpass.getpass(prompt="password for %s: " % user_name)

SERVER_IP = "192.168.1.201"
SERVER_PORT = 10000

hosts = ([
        ('raspi5', {'ssh_hostname': '192.168.1.202'}),
        ('radxax4', {'ssh_hostname': '192.168.1.200'}),
        ],
        {"ssh_user": user_name,
         "ssh_password": PASSWORD,
         "_sudo_password": PASSWORD,
         "server_ip": SERVER_IP,
         "server_port": SERVER_PORT,
         }
)

