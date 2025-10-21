# Install OS image

For the Raspberry PI 5:
1. Get image for the device from [Dietpi](https://dietpi.com/) and extract it<br>
'''
wget https://dietpi.com/downloads/images/DietPi_RPi5-ARMv8-Trixie.img.xz
xz -d DietPi_RPi5-ARMv8-Trixie.img.xz
'''

Prepare and write the image to SD card:
'''
sudo dd if=DietPi_RPi5-ARMv8-Trixie.img of=/dev/<sdX>
sudo mount -t auto /dev/<sdX>1 /mnt/tmp/
sudo patch /mnt/tmp/dietpi.txt patches/dietpi_raspi5.patch
sudo umount /mnt/tmp/
'''

Insert SD card into device and boot.
