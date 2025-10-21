import getpass

user_name = "dietpi"
PASSWORD = getpass.getpass(prompt="password for %s: " % user_name)

hosts = ([
	    ('raspi5', {'ssh_hostname': '192.168.1.202'}),
        ],
        {"ssh_user": user_name,
         "ssh_password": PASSWORD,
         "_sudo_password": PASSWORD,
         }
)

