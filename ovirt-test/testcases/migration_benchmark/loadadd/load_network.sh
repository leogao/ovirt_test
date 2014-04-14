#!/bin/bash

dest_ip=$1
load()
{
	while true; do 
		ping -l 100000 -q -s 10 -f $dest_ip >/dev/null 2>&1
	done
}

if [[ $# -ne 1 ]]; then
	echo "Usage: `basename $0` options (ip)";
else
	load &
fi
