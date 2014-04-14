#! /bin/sh

mkdir -p /etc/libvirt/hooks
chmod 755 /etc/libvirt/hooks

cp qemu /etc/libvirt/hooks/
chmod 755 /etc/libvirt/hooks/qemu
