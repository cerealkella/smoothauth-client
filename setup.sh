#!/bin/bash
echo "Creating udev rule to allow pyusb to communicate with card reader."
echo "Will need to run this with sudo."
if [ -e /etc/udev/rules.d/95-usb-perms.rules ]; then
  echo "File already exists!"
else
  echo "SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"0c27\", ATTR{idProduct}==\"3bfa\", GROUP=\"plugdev\", MODE=\"0666\"" >> /etc/udev/rules.d/95-usb-perms.rules
  echo "File written."
fi
echo "Now installing dependencies..."
sudo apt install git python3-pip python3-wheel python3-setuptools python3-dev build-essential dpkg-dev libgtk-3-dev libwebkit-dev freeglut3-dev libgstreamer-plugins-base1.0-dev
