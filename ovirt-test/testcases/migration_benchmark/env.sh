#!/bin/bash

GbE10="eth6"

up_gbe10()
{
	ifconfig $GbE10 up
	sleep 2
	ifconfig $GbE10 10.0.1.10
	sleep 2
}

down_gbe10()
{
	ifconfig $GbE10 0
	sleep 2
	ifconfig $GbE10 down
	sleep 2
}


create_pool()
{
	virsh pool-define nfs_pool.xml
	sleep 2
	virsh pool-start nfs_pool
	sleep 2
}

restart_vdsmd()
{
	sleep 2
	service vdsmd reconfigure
	sleep 2
	service vdsmd restart
}

clean()
{
	umount /data/images
	sleep 2
	virsh pool-destroy nfs_pool
	sleep 2
	virsh pool-undefine nfs_pool
	sleep 2
}

create_br()
{
	#ovs-vsctl add-br br-ovp
	brctl addbr br-ovp
	brctl addif br-ovp $GbE10
	ifconfig br-ovp 10.0.1.10
	ifconfig $GbE10 0
}

clean_br()
{
	#ovs-vsctl del-br br-ovp
	brctl delif br-ovp $GbE10
	ifconfig br-ovp down
	brctl delbr br-ovp
}

if [[ X$1 == X'clean' ]]; then
	clean
	down_gbe10
	clean_br
else
	if [[ X$1 == X'vdsmd' ]]; then
		restart_vdsmd
	fi
	up_gbe10
	create_pool
	create_br
fi
