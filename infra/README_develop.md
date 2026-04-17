# Controller
The controller has no internet connection.
The only way to login is via ssh.

Pip needs an internet connection to work.

In a first terminal SSS into controller.
ssh -D 9999 <user>@<developer machine>

In a second terminal SSS into controller, too.
pip install tabulate --proxy socks5h://localhost:9999
