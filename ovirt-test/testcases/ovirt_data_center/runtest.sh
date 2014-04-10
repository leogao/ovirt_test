#!/bin/bash
# A test script for vdsm storage domain.
# create storage domain using nfs type.
# here implement script to run those cases.
# author: wei.gao
 
source /opt/wr-test/testcases/ovp/common_lib/testlib.sh
BOOT_TIME="0"
CASESARRAY=""
FAILARRAY=""
ENGINE_LOG="/var/log/ovirt-engine/engine.log"
TEST_PY="test.py"

recordResult()
{
        retVal=$?
        cName=$1
        CASESARRAY+=" $cName"
        if [[ $retVal -ne 0 ]]; then 
                FAILARRAY+=" $cName"
                # attach the ovirt-engine service logs
                print_summary "engine.log"
                [[ -s $ENGINE_LOG ]] && cat $ENGINE_LOG
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
        print_summary "do create/clean data-centers \n"
        python $TEST_PY $IP
        recordResult "do_create_clean_data-centers"
        result_summary "ovirt data-centers(create/remove) testing"
}

ONLY_HOST=1
start_test
