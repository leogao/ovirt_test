#!/bin/bash
# A test script for vdsm storage domain.
# create storage domain using nfs type.
# here implement script to run those cases.
# author: wei.gao

source /opt/wr-test/testcases/ovp/common_lib/testlib.sh
CPUTYPE_SH='cputype.sh'
REMOETE_RUN='/opt/wr-test/testcases/ovp/common_lib/remote_run.py'
BOOT_TIME="0"
CASESARRAY=""
FAILARRAY=""
HOST_DEPLOY_DIR="/var/log/ovirt-engine/host-deploy"
TEST_PY="test.py"
DEFAULT_IP='128.224.158.211'
NODE_IP='128.224.159.148'

# NODES_IP='ip1 ip2 ip3'
EG_IP=${ENGINE_IP:-$DEFAULT_IP}
NDS_IP=${NODES_IP:-$NODE_IP}
NODES=''
CPU_TYPE=''

get_cputype()
{
cat > ${CPUTYPE_SH} << EOF
#!/bin/bash
# cputype.sh want to got cpu info: 
#
# CPU_TYPE='Intel Conroe Family'
# CPU_TYPE='Intel Nehalem Family'
# CPU_TYPE='Intel Penryn Family'
# CPU_TYPE='Intel Westmere Family'
# CPU_TYPE='Intel SandyBridge Family'
# CPU_TYPE='Intel Haswell'

CPU_ID="\`grep -e "microcode:.*sig" /var/log/kern.log | grep CPU | awk -F "sig=|," '{print \$2}' | uniq\`"
    case \$CPU_ID in
        '0x306c3')
            CPU_TYPE=Basking-Ridge ;;
        '0x306c2')
            CPU_TYPE=Lava-Canyon ;;
        '0x40650')
            CPU_TYPE=Whitetip-Mountain-1 ;;
        '0x306a5'|'0x306a8')
            CPU_TYPE=Sabino-Canyon ;;
        '0x206a6')
            CPU_TYPE=Stargo ;;
        '0x206d5'|'0x206d7')
            # Canoe-Pass ;;
            CPU_TYPE='Intel SandyBridge Family' ;;
        '0x306e4')
            # Canoe-Pass-Ivy-Refresh ;;
            CPU_TYPE='Intel SandyBridge Family' ;;
        '0x206a7')
            CPU_TYPE=EVOC-EC7-1817LNAR ;;
        '0x206a5'|'0x206a2')
            CPU_TYPE=Emerald-Lake ;;
        '0x20655')
            CPU_TYPE=MATXM-CORE-411-B ;;
        '0x20652')
            CPU_TYPE=Red-Fort ;;
        '0x206c2')
            CPU_TYPE=Greencity ;;
        '0x106a5')
            CPU_TYPE=Hanlan-Creek ;;
        '0x106e2'|'0x106e4')
            CPU_TYPE=Osage ;;
        '0x1067a')
            # Super_Micro ;;
            CPU_TYPE='Intel Penryn Family' ;;
        '0x206d6')
            # Oak-Creek-Canyon ;;
            CPU_TYPE=Oak-Creek-Canyon ;;
        '0x6fb')
            # dell755 ;;
            CPU_TYPE='Intel Conroe Family' ;;
         *)
            CPU_TYPE='None' ;;
    esac
echo "CPU_TYPE=\$CPU_TYPE"
EOF
        IP=$1
        python $REMOETE_RUN -i $IP -f scp -m $CPUTYPE_SH 
        python $REMOETE_RUN -i $IP -f ssh_run -e "bash $CPUTYPE_SH" > cputype.log
        CPU_TYPE=$(grep CPU_TYPE cputype.log |awk -F= '{print $2}' |sed 's/\r//g')
}

format_nodes()
{
        for ip in ${NDS_IP} ; do
            echo $ip
            get_cputype $ip
	    if [[ -z ${NODES} ]]; then
		NODES="$ip:$CPU_TYPE"
	    else
		NODES+=",$ip:${CPU_TYPE}"
	    fi
        done
}

recordResult()
{
        retVal=$?
        cName=$1
        CASESARRAY+=" $cName"
        if [[ $retVal -ne 0 ]]; then 
                FAILARRAY+=" $cName"
                # attach the ovirt-engine service logs
                print_summary "host-deploy log"
                HOST_DEPLOY_LOG=$(ls ${HOST_DEPLOY_DIR}/ovirt-*)
                [[ -s $HOST_DEPLOY_LOG ]] && cat $HOST_DEPLOY_LOG
                echo "***********EOF***********"
                echo ""
        fi
}

result_summary()
{
        Summary=$1
        print_summary "All cases summary"
        for kcase in $CASESARRAY; do
                if [[ `echo $FAILARRAY | grep $kcase` ]]; then
                        echo "fail ------ $kcase"
                else
                        echo "pass ------ $kcase"
                fi
        done
        if [[ $FAILARRAY = "" ]];then
                pass_status $Summary
        else
                print_summary "Failed cases summary"
                for jcase in $FAILARRAY; do
                        echo "fail ------ $jcase"
                done
                fail_status $Summary
        fi
}

get_ip()
{
        Gateway=$(netstat -r | grep 'default' | awk '{ print $2}')
        Filter=$(echo $Gateway | awk -F. {'print $1"."$2"."$3'})
        IP=$(ifconfig | grep 'inet addr:'| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}' | grep $Filter)
        echo "IP=$IP Gateway=$Gateway"
}

        
host_handle()
{
        get_ip
        format_nodes
        rm -rf ${HOST_DEPLOY_DIR}/*
        print_summary "do create/clean clusters \n"
        echo "python $TEST_PY $EG_IP \"${NODES}\""
        python $TEST_PY $EG_IP "${NODES}"
        recordResult "do_create_clean_clusters"
        result_summary "ovirt clusters(create/remove) testing"
}

ONLY_HOST=1
start_test
