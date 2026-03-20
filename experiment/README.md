[![Pylint](https://github.com/rsie-dev/power_measurement/actions/workflows/pylint.yml/badge.svg)](https://github.com/rsie-dev/power_measurement/actions/workflows/pylint.yml)

# Overview
Small framework to collect electrical and system metrics of SBC devices.

# Develop
Developer informations can be found [here](docs/develop.md).

# Install
```
python3 -m venv venv
venv/bin/pip install power-measurement-experiment
```

## Running under normal user (non-root)
### Create USB group:
```shell
sudo addgroup usbmeter
```

### Install udev rules:
```shell
sudo install --mode=0644 --target-directory=/etc/udev/rules.d/ udev/90-usb-power-meter.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

This provides access for users of the usbmeter group.
Do not forget that after beeing added to the group the user has to logout and login again.


# Usage
Usage informations can be found [here](docs/usage.md).
