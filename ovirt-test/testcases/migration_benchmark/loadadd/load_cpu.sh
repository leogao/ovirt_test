#!/bin/sh
##echo user nice system idle iowait irq softirq

printUsage ()
{
	cat <<-EOF >&1
	usage: ./${0##*/} [cpu_number] [us] [-h] 
	cpu_number : load the cpu1
	us : sleep the several "us" during the load, default is 10240us, 10 micro second
	-h : Print this menu
	example: ${0##*/} : ./load-cpu.sh cpu1 1024
EOF
	exit 0
}


while getopts 'h' OPTION 
do 
case $OPTION in 
h) printUsage
	exit 0;
	;; 
esac 
done 

if [ -z $1 ]; then
	echo "must assign a cpu number, ./load-cpu.sh cpu1, etc"
	exit 0
fi



if [ -z $2 ]; then
	us=10240
else
	us=$2
fi


taskset -c `echo $1 | sed 's/cpu//g'` ./eatme-sleep $us &
pid=$$

CPULOG_1=$(cat /proc/stat | grep -i "$1 " | awk '{print $2" "$3" "$4" "$5" "$6" "$7" "$8}')
SYS_IDLE_1=$(echo $CPULOG_1 | awk '{print $4}')
Total_1=$(echo $CPULOG_1 | awk '{print $1+$2+$3+$4+$5+$6+$7}')
 
sleep 15
 
CPULOG_2=$(cat /proc/stat | grep -i "$1 " | awk '{print $2" "$3" "$4" "$5" "$6" "$7" "$8}')
SYS_IDLE_2=$(echo $CPULOG_2 | awk '{print $4}')
Total_2=$(echo $CPULOG_2 | awk '{print $1+$2+$3+$4+$5+$6+$7}')
 
SYS_IDLE=`expr $SYS_IDLE_2 - $SYS_IDLE_1`
 
Total=`expr $Total_2 - $Total_1`
SYS_USAGE=`expr $SYS_IDLE/$Total*100 |bc -l`
 
SYS_Rate=`expr 100-$SYS_USAGE |bc -l`
 
Disp_SYS_Rate=`expr "scale=3; $SYS_Rate/1" |bc`
echo "$1 usage: " $Disp_SYS_Rate%
