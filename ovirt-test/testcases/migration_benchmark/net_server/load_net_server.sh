#!/bin/bash

dest_ip=$1
load()
{
	python migrate_net_downtime.py server $dest_ip >/dev/null 2>&1
}

if [[ $# -ne 1 ]]; then
	echo "Usage: `basename $0` options (ip)";
else
	load &
fi
