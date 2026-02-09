# Install OS image

Instrcutions are based on Dietpi v9.18 which is based on debian 13 (trixie).

## Raspberry PI 5
1. Get image for the device from [Dietpi](https://dietpi.com/) and extract it<br>
'''
wget https://dietpi.com/downloads/images/DietPi_RPi5-ARMv8-Trixie.img.xz
xz -d DietPi_RPi5-ARMv8-Trixie.img.xz
'''
1. Prepare and write the image to SD card:
'''
sudo dd if=DietPi_RPi5-ARMv8-Trixie.img of=/dev/<sdX>
sudo mount -t auto /dev/<sdX>1 /mnt/tmp/
sudo patch /mnt/tmp/dietpi.txt patches/dietpi_raspi5.patch
sudo umount /mnt/tmp/
'''
1. Insert SD card into device and boot.
1. Wait till initial setup and update are through
1. Continue with custom setup in ../infra

## VisionFive2
1. Get image for the device from [Dietpi](https://dietpi.com/) and extract it<br>
'''
wget https://dietpi.com/downloads/images/DietPi_VisionFive2-RISC-V-Trixie.img.xz
xz -d DietPi_VisionFive2-RISC-V-Trixie.img.xz
'''
1. Prepare and write the image to SD card:
'''
sudo dd if=DietPi_RPi5-ARMv8-Trixie.img of=/dev/<sdX>
sudo mount -t auto /dev/<sdX>1 /mnt/tmp/
sudo patch /mnt/tmp/dietpi.txt patches/dietpi_visionfive2.patch
sudo umount /mnt/tmp/
'''
1. Insert SD card into device and boot.

## Radxa X4
1. [Update BIOS if needed](https://docs.radxa.com/en/x/x4/bios/update-bios)
1. Get X68_64 UEFI installer image for the device from [Dietpi](https://dietpi.com/)
1. Prepare USB stick to boot
1. Boot from USB stick and install system -> power off
1. Prepare initial USB stick with live linux system
1. Boot from USB stick
1. Copy patches/dietpi_radxax4.txt to separate USB stick
1. Mount separate USB stick to /mnt/tmp
1. Mount /dev/mmcblk0p1 to /mnt/boot
1. Copy /mnt/tmp/dietpi_radxax4.txt to /mnt/boot/boot/dietpi.txt
1. Power off
1. Remove both USB sticks
1. Boot device

