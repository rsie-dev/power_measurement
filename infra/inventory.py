import getpass

PASSWORD = getpass.getpass(prompt="Password: ")

hosts = ([
	    ('raspi5', {'ssh_hostname': '192.168.1.10'}),
        ],
        {"ssh_user": getpass.getuser(),
         "ssh_password": PASSWORD,
         "_sudo_password": PASSWORD,
         }
)

