import getpass

PASSWORD = getpass.getpass(prompt="Password (dietpi): ")

hosts = ([
	    ('raspi5', {'ssh_hostname': '192.168.1.202'}),
        ],
        {"ssh_user": "dietpi",
         "ssh_password": PASSWORD,
         "_sudo_password": PASSWORD,
         }
)

