#!/bin/bash

start()
{
	virsh define vm1.xml
	sleep 2
	virsh start vm1
}

clean()
{
	virsh destroy vm1
	sleep 2
	virsh undefine vm1
}

if [[ X$1 == X'clean' ]]; then
	clean
else
	start
fi
