#!/bin/bash
LO_NAME=$1
RE_NAME=$2
RE_FLAG=$3

echo "127.0.0.1 localhost.localdomain           localhost" > /etc/hosts
echo "10.0.1.10       $LO_NAME.wrs.com       $LO_NAME" >> /etc/hosts
echo "10.0.1.12       $RE_NAME.wrs.com       $RE_NAME" >> /etc/hosts

if [[ $# -gt 2 ]]; then
    echo "$RE_NAME" > /etc/hostname
    hostname $RE_NAME
else
    echo "$LO_NAME" > /etc/hostname
    hostname $LO_NAME
fi
