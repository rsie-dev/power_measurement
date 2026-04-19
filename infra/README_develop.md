# Controller

## Problem
The controller has no internet connection.
The only way to login is via ssh.
But pip needs an internet connection to work.

## Solution
Login to the controller via ssh while enabling the remote SOCKS5 proxy:
```
ssh -R 9999 -l <user> 192.168.5.1
```

## PIP
Create an virtual environment using the system packages:
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
