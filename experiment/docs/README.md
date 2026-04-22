# Overview
Small framework to collect electrical and system metrics of SBC devices.

# Develop
Developer informations can be found [here](develop.md).

## Running under normal user (non-root)
### Create USB group:
```shell
sudo addgroup usbmeter
```

### Install udev rules:
```shell
sudo install --mode=0644 --target-directory=/etc/udev/rules.d/ venv/lib/python3.12/site-packages/usb_multimeter/udev/90-usb-power-meter.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

This provides access for users of the usbmeter group.
Do not forget that after beeing added to the group the user has to logout and login again.


# Usage
Usage informations can be found [here](usage.md).

# API
API reference can be found [here](api.md).
