#! /bin/sh
TIME_IP=147.11.100.50
TIME_ZONE=Hong_Kong
#TIME_ZONE=New_York

cd "/etc"


sed -i -e "s/time.server.example.com/$TIME_IP/" ntp.conf

rm -f localtime
cp "../usr/share/zoneinfo/Asia/$TIME_ZONE" localtime
#cp "../usr/share/zoneinfo/America/$TIME_ZONE" localtime

cd -

exit 0
