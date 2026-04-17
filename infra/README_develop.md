# Controller

## PIP
### Problem
The controller has no internet connection.
The only way to login is via ssh.
But pip needs an internet connection to work.

### Solution
In a first terminal SSH into controller:
```
ssh 192.168.5.1
```

Then create a local SOCKS proxy:
```
ssh -D 9999 <user>@<developer machine IP>
```

In a second terminal SSH into controller, too.
```
ssh 192.168.5.1
```

Then create an virtual environment and packages:
```
python3 -m venv --system-site-packages venv

venv/bin/pip install --proxy socks5h://localhost:9999 power-measurement-experiment
```

## git
Add / update github entry in ~/.ssh/config
```
Host github.com
  HostName github.com
  User git
  ProxyCommand nc -x 127.0.0.1:9999 %h %p
```