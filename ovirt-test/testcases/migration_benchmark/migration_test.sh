#!/bin/bash

help()
{
	echo "Usage: `basename $0` options (-i ip) (-d X[ms]) (-r Y[s]) [-c] -h for help";
}

migrate()
{
	time virsh migrate --live --p2p --verbose vm1 $COMPRESSED qemu+tcp://${DEST_IP}/system
}

if ( ! getopts "i:ch" opt); then
	help
	exit 1;
fi

while getopts "i:d:r:mch" opt; do
	case $opt in
		i) DEST_IP=$OPTARG;;
		d) DOWNTIME_THRESHOLD_MS=$OPTARG;;
		r) RUNTIME_THRESHOLD_S=$OPTARG;;
		m) migrate
		   exit 0 ;;
		c) COMPRESSED='--compressed' ;;
		h) help
		   exit 0;;
	esac
done

DF_IP="10.0.1.12"
DEST_IP=${DEST_IP:-$DF_IP}
MIGRATE_CMD="bash $0 $@ -m"


virt_downtime()
{
	sleep 3
	elem_data=$(egrep '"status": "completed", "downtime":' /var/log/libvirtd.log | tail -1 |  grep buf= | awk -Fbuf= '{print $2}')
	if [[ X$elem_data != X ]]; then
		cat > /tmp/elem_analyze.py << EOF
#!/usr/bin/env python
elem_dict = ${elem_data}
if elem_dict != '':
	print elem_dict['return']['downtime']
else:
	print None
EOF
		DOWNTIME=$(python /tmp/elem_analyze.py)
	else
		DOWNTIME='0'
	fi
	echo "downtime_virt: $DOWNTIME milliseconds"
}

hooks_action()
{
	# count downtime
	migrate_t=$(grep migrate     migrate.log | awk '{print $4}')
	prepare_t=$(grep prepare     migrate.log | awk '{print $4}')
	start_t=$(grep 'start start' migrate.log | awk '{print $4}')
	started_t=$(grep started     migrate.log | awk '{print $4}')

	# 1. migration time
	m_time=$(awk 'BEGIN{print '$start_t'-'$migrate_t'}')
	# 2. Calculate downtime + libvirt overhead
	c_time=$(awk 'BEGIN{print '$started_t'-'$start_t'}')
	# 3. Overhead for libvirt
	o_time=$(awk 'BEGIN{print '$start_t'-'$prepare_t'}')
	# Downtime 
	d_time=$(awk 'BEGIN{print '$c_time'-'$o_time'}')

	#echo $(($m_time/1000000))
	#echo $(($c_time/1000000))
	#echo $(($o_time/1000000))
	#echo $(($d_time/1000000))
	echo "DOWNTIME: $d_time milliseconds"
}

ping_action()
{
	interval=0.001
	# start ping
	if [[ X$1 = X'start' ]]; then
		VM_IP=${VM_IP:-'10.0.1.3'}
		ping -q -i $interval $VM_IP > ping.elem &
		PING_PID=$(echo $!)
		echo $PING_PID
		#exit 0
	elif [[ X$1 = X'end' ]]; then
		# abort ping and get loss packets to count interrupt time.
		# PING_PID=$(pidof ping)
		kill -2 $PING_PID
		# cat ping.elem

		all=$(grep 'packets transmitted' ping.elem | awk '{print $1}')
		rev=$(grep 'packets transmitted' ping.elem | awk '{print $4}')
		loss=$(awk 'BEGIN{print '$all'-'$rev'}')

		LOSSTIME=$(awk 'BEGIN{print '$loss'*'$interval'*'1000'}')
		echo "losstime: $LOSSTIME milliseconds"
		#exit 0
	else
		echo "Usage: `basename $0` options [start] [end]";
	fi
}

net_delay()
{

	MIGRATE_NET_CLIENT_CMD="python net_server/migrate_net_downtime.py client $VM_IP $DOWNTIME_THRESHOLD_MS $RUNTIME_THRESHOLD_SEC > net_downtime.elem & PID=\$(echo \$!); echo 'pid='\$PID"
	MIGRATE_NET_CLIENT='migrate_net_client.py'
cat > $MIGRATE_NET_CLIENT << EOF
#!/usr/bin/env python
import sys
sys.path.append('../common_lib/')
import pexpect

def main():
    try:
        bash_session  = pexpect.spawn('bash')
	bash_session.logfile = sys.stdout
        index = bash_session.expect(['root@.*#','bash-4.2#', pexpect.EOF], timeout=60)
        if index == 0 or index == 1:
	    migrate_net_delay_cmd = "${MIGRATE_NET_CLIENT_CMD}"
            bash_session.sendline(migrate_net_delay_cmd)
        index = bash_session.expect(['pid=', pexpect.EOF], timeout=60)
        if index == 0:
	    migrate_cmd = "${MIGRATE_CMD}"
            bash_session.sendline(migrate_cmd)
        index = bash_session.expect(['sys	', pexpect.EOF], timeout=60)
        if index == 0:
            bash_session.sendline('kill -s INT %1')
        index = bash_session.expect(['KeyboardInterrupt', pexpect.EOF], timeout=60)
        if index == 0:
            print  'migrate finished and got net_delay successfully'
    except Exception,e:
        print  'bash_session_run -> unexpected issue:' % (e)
    bash_session.sendline('exit')
    bash_session.terminate()
if __name__ == '__main__':
    main()
EOF
}

net_downtime()
{
	# client start
	VM_IP=${VM_IP:-'10.0.1.3'}

	net_delay
	python $MIGRATE_NET_CLIENT

	cat net_downtime.elem
	NET_DOWNTIME=$(grep 'Updated maximum network delay:' net_downtime.elem | tail -1 | awk '{print $5}')
	echo "downtime_net: $NET_DOWNTIME milliseconds"
}


DOWNTIME_THRESHOLD_MS=8000
RUNTIME_THRESHOLD_SEC=600

#ping_action start

net_downtime 
#virt_downtime

#hooks_action
#ping_action end
