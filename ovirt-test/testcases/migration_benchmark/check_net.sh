#!/bin/bash
# Check 2 machine's network interface connected.
# auth: Leo gao

usage() { 
    echo "Usage: $0 [-u ;; up all net interface]" 
    echo "Usage: $0 [-f ;; filter all net linked interfance]"
    echo "Usage: $0 [-c ;; connect the remote IP]"
    exit 1
}

# Verify that the parameter passed is an IP Address:
function is_IP() {
    if [ `echo $1 | grep -o '\.' | wc -l` -ne 3 ]; then
        echo "Parameter '$1' does not look like an IP Address (does not contain 3 dots)."
        exit 1
    elif [ `echo $1 | tr '.' ' ' | wc -w` -ne 4 ]; then
        echo "Parameter '$1' does not look like an IP Address (does not contain 4 octets)."
        exit 1
    else
        for OCTET in `echo $1 | tr '.' ' '`; do
            if ! [[ $OCTET =~ ^[0-9]+$ ]]; then
                echo "Parameter '$1' does not look like in IP Address (octet '$OCTET' is not numeric)."
                exit 1
            elif [[ $OCTET -lt 0 || $OCTET -gt 255 ]]; then
                echo "Parameter '$1' does not look like in IP Address (octet '$OCTET' in not in range 0-255)."
                exit 1
            fi
        done
    fi
    return 0
}

VETHX=''
VETHXS=''
function up_gbe10() {
        VETHXS=''
	UPETHXS=$(ifconfig | grep ^eth | awk '{print $1}')
	ETHXS=$(ifconfig -a | grep ^eth | awk '{print $1}')
	for i in $ETHXS; do
		ethtool $i | grep FIBRE >/dev/null
		if [[ $? -eq 0 ]] ; then 
			ifconfig $i up >/dev/null
                        VETHXS+=" $i"
                elif [[ $UPETHXS != *$i* ]]; then
			ifconfig $i down >/dev/null
		fi
		sleep 1
	done
}

filter_gbe10() {
        up_gbe10
	for i in $VETHXS; do
		ifconfig $i up >/dev/null
		sleep 1
		ethtool $i | grep Link | grep yes >/dev/null
		if [[ $? -ne 0 ]] ; then 
			ifconfig $i down
			:;
		else
			ethtool $i | grep FIBRE >/dev/null
			[[ $? -eq 0 ]] && VVETHXS+=" $i"
		fi
	done
	echo $VVETHXS
}

check_connect()
{
        ethx=$1
        ip=$RemoteIP
	tag=$(echo $ip |awk -F. '{print $4 + 1}')
	for ((i=1;i<=200;i++)); do
		local_ip=$(echo $ip| awk -F. '{print $1"."$2"."$3}')".$tag"
		ping -c 3 $local_ip >/dev/null
		[[ $? -ne 0 ]] && break
		tag=$(($tag +1))
	done
	ifconfig $ethx $local_ip
	sleep 1
	ping -c 5 -I $ethx $ip >/dev/null
	if [[ $? -ne 0 ]]; then
		ifconfig $ethx 0
		ifconfig $ethx down
	else
		EETHX=$ethx
	fi
	echo $EETHX
}

check_loop() {
        filter_gbe10
	for i in $VVETHXS; do
            check_connect $i
        done
}

[ $# -eq 0 ] && usage
while getopts ":ufc:" flag; do
    case "${flag}" in
        c)
            RemoteIP=${OPTARG}
            is_IP $RemoteIP || usage
            echo "Run connected ethx"
            check_loop
            ;;
        u)
            echo "Run ifconfig ethx up"
            up_gbe10
            ;;
        f)
            echo "Run filter GBE10"
            filter_gbe10
            ;;
        *)
            usage
            ;;
    esac
done
shift $((OPTIND-1))
