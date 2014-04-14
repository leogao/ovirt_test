#!/bin/bash

machine='IronPass'

COMPRESSED='yes'
CPULOAD='yes'
NETLOAD='yes'

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

report_file=${machine}_migrate_${prefix}.report


A=10

echo $A/2

