#! /bin/sh

migrate_t=$(grep migrate /tmp/migrate.log | awk '{print $4}')
prepare_t=$(grep prepare /tmp/migrate.log | awk '{print $4}')
start_t=$(grep 'start start' /tmp/migrate.log | awk '{print $4}')
started_t=$(grep started /tmp/migrate.log | awk '{print $4}')

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
