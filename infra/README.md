# OS configuration
This file contains instructions for configuring the operating system using pyinfra on the SBC devices 
used as devices under test, as well as on the controller computer used for energy consumption measurements.

The commands provided in this document are intended to be executed on a Debian-based Linux system.

Prepare the devices by installing the OS (see ../os_install/README.md).
After the OS installation, all devices should be running on the local network and reachable 
via ssh and the dietpi user.

## Preparation
Adapt for all devices in the **inventory.py** file the current IP address and 
for all devices under test the MAC address, too.

## Controller

### Add users
To add users during the installation copy the users public key ssh file to the _ssh_keys_ folder.
The public key must be named after the user like: _user_ed25519.pub_
This will create a user named "user" with password "user".
The ssh key can be used to log in via ssh.
The password can be changed immediately after the configuration before the first reboot.
Afterwards the filesystem is mounted read-only.

### Data files
Data files needed for the energy measurements can be placed in the *data* folder.
The content of the data folder will be copied to the */data* folder of the controller.

### Configuration
To configure the controller device execute:
```
./pyinfra.sh inventory.py deploy.py --limit controller --data use_proxy=False --data sync_data=True
```

### Acvtivate DHCP
To prevent conflicts with existing dhcp servers in the network, 
the dhcp server is not automatically active after installation.

To activate the DHCP server:
1. Login to the controller as user dietpi via ssh
2. Edit as root (sudo) */etc/default/isc-dhcp-server*
Uncomment the line:
#INTERFACESv4="eth0"
3. Edit as root (sudo) */etc/network/interfaces*
Comment all lines after _# Ethernet_ up to the line _# BEGIN PYINFRA BLOCK_.
Uncomment all the lines after _# BEGIN PYINFRA BLOCK_. up to the line _# END PYINFRA BLOCK_.

After the next boot the controller will have the IP address 192.168.5.1 and acting as DHCP server.

## Devices under test
To configure an device under test execute:
```
./pyinfra.sh inventory.py deploy.py --limit <device> --data use_proxy=False
```
Where device is the name of the device under test as in the inventory.py file e.g. _raspi5_.

## Post configuration
Shut down all devices.
Revert the changes to the **inventory.py** file.
Connect all devices to an independent network.
The controller will work as an DHCP server and will have the IP address _192.168.5.1_.

## Configuration changes
To later update the configuration these steps are required:
1. Connect your computer to the independent network.
2. Login to the device with ssh and create an reverse proxy:
```
ssh -R 9999 -l <user> <device>
```
Keep this connection open.
3. Update the configuration by executing:
```
./pyinfra.sh inventory.py deploy.py --limit <device> --data use_proxy=True
```
To additionally synchronize the data folder on the controller add: --data sync_data=True
4. Reboot the device
