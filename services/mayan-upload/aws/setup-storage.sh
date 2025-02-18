#!/bin/bash

set -x
set -e  # Exit on error

# Detect the new unmounted SSD (assuming it's the only one)
NEW_DISK=$(lsblk -ndo NAME,TYPE | awk '$2=="disk"' | grep -v "$(lsblk -ndo PKNAME,MOUNTPOINT | grep -v '\[' | awk '{print $1}')" | head -n1)

if [ -z "$NEW_DISK" ]; then
    echo "No unmounted SSD detected. Exiting."
    exit 1
fi

DEVICE="/dev/$NEW_DISK"
MOUNT_POINT="/var/lib/docker"

echo "Using $DEVICE for Docker storage."

# Ensure the device exists
if [ ! -b "$DEVICE" ]; then
    echo "Device $DEVICE not found. Exiting."
    exit 1
fi

# Check if the disk is already formatted
if ! blkid "$DEVICE" | grep -q "TYPE="; then
    echo "Formatting $DEVICE as ext4..."
    sudo mkfs -t ext4 "$DEVICE"
else
    echo "$DEVICE is already formatted."
fi

# Stop Docker service
echo "Stopping Docker..."
sudo systemctl stop docker

# Create mount point if it doesn't exist
if [ ! -d "$MOUNT_POINT" ]; then
    sudo mkdir -p "$MOUNT_POINT"
fi

# Mount the new disk
echo "Mounting $DEVICE to $MOUNT_POINT..."
sudo mount "$DEVICE" "$MOUNT_POINT"

# Move existing Docker data
echo "Moving existing Docker data to new drive..."
sudo rsync -aAX /var/lib/docker/ "$MOUNT_POINT/"

# Verify the copy before removing old data
if [ $? -eq 0 ]; then
    echo "Docker data successfully copied. Removing old data..."
    sudo rm -rf /var/lib/docker/*
else
    echo "Error copying data. Exiting."
    exit 1
fi

# Unmount to update fstab
echo "Updating /etc/fstab..."
UUID=$(blkid -s UUID -o value "$DEVICE")
echo "UUID=$UUID $MOUNT_POINT ext4 defaults,nofail 0 2" | sudo tee -a /etc/fstab

# Remount and verify
echo "Remounting..."
sudo mount -a

# Restart Docker
echo "Restarting Docker..."
sudo systemctl start docker

echo "Setup complete! Docker is now using $DEVICE for storage."
