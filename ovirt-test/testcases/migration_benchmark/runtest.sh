#! /bin/sh

LOCAL_IP='10.0.1.10'
REMOTE_IP='10.0.1.12'
VM_IP='10.0.1.3'
VM2_IP='10.0.1.4'

REMOTE_RUN="python /opt/wr-test/testcases/ovp/common_lib/remote_run.py"
log_path=${log_path:-'./logs'}
data_name='data_raw.log'
backdata_name='backdata_raw.log'

machine='IronPass'
prefix=${machine}

COMPRESSED='yes'
CPULOAD='yes'
NETLOAD='yes'

WAITTIME=10

mkdir -p $log_path

#------------------------------------------------------------------------------
wait_vm_up()
{
	for((j=30;j>0;j--)); do
		ping -c 2 $VM_IP >/dev/null 2>&1
		[[ $? -eq 0 ]] && break
		sleep 1
	done
	[[ j -eq 0 ]] && return 1
}

clean_vm()
{
	virsh destroy vm1
	sleep $(($WAITTIME/2))
}

create_vm()
{
	for((j=30;j>0;j--)); do
		virsh create vm1.xml
		wait_vm_up
		[[ $? -ne 0 ]] && break
		clean_vm
	done
}


prepare_vm()
{
	create_vm
	$REMOTE_RUN -i $VM_IP -f scp -m net_server/migrate_net_downtime.py  
	$REMOTE_RUN -i $VM_IP -f scp -m net_server/load_net_server.sh  
	$REMOTE_RUN -i $VM_IP -f ssh_run -e "bash load_net_server.sh $VM_IP"

	if [[ X$CPULOAD = X'yes' ]]; then
		$REMOTE_RUN -i $VM_IP -f scp -m loadadd/load_cpu.sh
		$REMOTE_RUN -i $VM_IP -f scp -m loadadd/eatme-sleep
		$REMOTE_RUN -i $VM_IP -f ssh_run -e "bash load_cpu.sh cpu0"
	fi
	if [[ X$NETLOAD = X'yes' ]]; then
		$REMOTE_RUN -i $VM_IP -f scp -m loadadd/load_network.sh
		$REMOTE_RUN -i $VM_IP -f ssh_run -e "bash load_network.sh $VM2_IP"
	fi
}

collect_data()
{
	prename
	data_file=${log_path}/${prefix}_${data_name}
	backdata_file=${log_path}/${prefix}_${backdata_name}
	
	#echo $data_file
	#return 

	echo > $data_file
	echo > $backdata_file
	COUNT=$1
	#MAX=$(awk 'BEGIN{print '$COUNT'/2}')
	MAX=$COUNT
	for((i=$COUNT;i>0;i--)); do
		echo "=== $i time migration ==="
		prepare_vm
		if [[ X$COMPRESSED = X'yes' ]]; then
			bash migration_test.sh -i $REMOTE_IP -c >> $data_file
		else
			bash migration_test.sh -i $REMOTE_IP >> $data_file
		fi
		$REMOTE_RUN -i $REMOTE_IP -f ssh_run -e "bash count.sh" >> $data_file
		$REMOTE_RUN -i $REMOTE_IP -f ssh_run -e "virsh destroy vm1" >> $data_file
		$REMOTE_RUN -i $REMOTE_IP -f ssh_run -e "rm -rf /tmp/migrate.log" >/dev/null
	done
}

prename()
{
	if [[ X$COMPRESSED = X'yes' ]]; then
		prefix+='_compressed'
	else
		prefix+='_no-compressed'
	fi
	if [[ X$CPULOAD = X'yes' ]]; then
		prefix+='_cpuload'
	else
		prefix+='_no-cpuload'
	fi
	if [[ X$NETLOAD = X'yes' ]]; then
		prefix+='_networkload'
	else
		prefix+='_no-networkload'
	fi
}

report()
{
	type=$1
	goback=$2
	[[ X$type = X'downtime_virt' ]] && return 0

	if [[ X$goback = X'go' ]]; then
		dfile=$data_file
	elif [[ X$goback = X'back' ]]; then
		dfile=$backdata_file
	else
		echo "Usage: `basename $0` options [downtime_virt/downtime_net] [go/back]"
		exit 1
	fi
	
	report_file=$log_path/${prefix}_${type}_${goback}.report

	#echo $report_file
	#return 

	# filter and count downtime
	rm -rf data.log
	if [[ X$type = X'downtime_virt' ]]; then
		cat $dfile |awk '/downtime_virt/' |tee -a data.log
	elif [[ X$type = X'downtime_net' ]]; then 
		cat $dfile |awk '/downtime_net/' |tee -a data.log
	elif [[ X$type = X'DOWNTIME' ]]; then 
		cat $dfile |awk '/DOWNTIME/' |tee -a data.log
	else
		echo "Usage: `basename $0` options [downtime_virt/downtime_net] [go/back]"
		exit 1
	fi

	echo "migrate between host-nodes $type results:" > ${report_file}
	sed -i 's/\r//g' data.log
	echo "-----------------------------" >> ${report_file}
	cat data.log >> ${report_file}
	echo "-----------------------------" >> ${report_file}
	echo "Samples=$MAX" >>  ${report_file}
	awk '
	(NR==1)		{min=$2;max=$2;typ=$3}
	($2<min)	{min=$2}
	($2>max)	{max=$2}
			{tot+=$2}
	END	{print "min: " min " " typ " avg: " tot/NR " " typ " max: " max " " typ }' data.log >>  ${report_file}
	sed -i 's/\r//g'  ${report_file}
}

#----------------------------------------

loop_count=4

do_test1()
{
	# no any load
	# no compressed migration 
	COMPRESSED='no'
	CPULOAD='no'
	NETLOAD='no'
	prefix=${machine}
	collect_data $loop_count
	report downtime_virt go
	report downtime_net go
}

do_test2()
{
	# no any load
	# compressed migration 
	COMPRESSED='yes'
	CPULOAD='no'
	NETLOAD='no'
	prefix=${machine}
	collect_data $loop_count
	report downtime_virt go
	report downtime_net go
}

do_test3()
{
	# with cpuload , no networking load
	# no compressed migration 
	COMPRESSED='no'
	CPULOAD='yes'
	NETLOAD='no'
	prefix=${machine}
	collect_data $loop_count
	report downtime_virt go
	report downtime_net go
}

do_test4()
{
	# with cpuload , no networking load
	# compressed migration 
	COMPRESSED='yes'
	CPULOAD='yes'
	NETLOAD='no'
	prefix=${machine}
	collect_data $loop_count
	report downtime_virt go
	report downtime_net go
}

do_test5()
{
	# no cpuload , with networking load
	# no compressed migration 
	COMPRESSED='no'
	CPULOAD='no'
	NETLOAD='yes'
	prefix=${machine}
	collect_data $loop_count
	report downtime_virt go
	report downtime_net go
}

do_test6()
{
	# with cpuload , no networking load
	# compressed migration 
	COMPRESSED='yes'
	CPULOAD='no'
	NETLOAD='yes'
	prefix=${machine}
	collect_data $loop_count
	report downtime_virt go
	report downtime_net go
}

do_test7()
{
	# with cpuload , with networking load
	# no compressed migration 
	COMPRESSED='no'
	CPULOAD='yes'
	NETLOAD='yes'
	prefix=${machine}
	collect_data $loop_count
	report downtime_virt go
	report downtime_net go
}

do_test8()
{
	# with cpuload , with networking load
	# compressed migration 
	COMPRESSED='yes'
	CPULOAD='yes'
	NETLOAD='yes'
	prefix=${machine}
	collect_data $loop_count
	report downtime_virt go
	report downtime_net go
}

#------------------------------------------------------------------------------

#loop_count=400
loop_count=50
#loop_count=1
WAITTIME=10
do_test1
do_test2
do_test3
do_test4
do_test5
do_test6
do_test7
do_test8
