# description : 
# This test VM migration for one node to another.
# non shared the images.
# virsh migrate with --copy-storage-inc or --copy-storage-all parameters.
# 
# Author : Wei.Gao 

#!/bin/bash
source /opt/wr-test/testcases/ovp/common_lib/testlib.sh
source /opt/wr-test/testcases/ovp/common_lib/migrate_lib.sh
source /opt/wr-test/env_var_file

export REMOETE_RUN="/opt/wr-test/testcases/ovp/common_lib/remote_run.py"
export EXPORTDIR="/export/data"
export POOL_NAME="nfs_pool"

RE_HOST='128.224.165.253'
[[ $# -ne 0 ]] && REMOTE_HOST=$1
export REMOTE_HOST=${REMOTE_HOST:-$RE_HOST}
# Path of guest image
export path_img="/var/lib/libvirt/images"
# Path of guest kernel
export path_kernel=$path_img
# Name of guest kernel
export guest_kernel="guest.kernel"
# Name of guest image
export guest_img_1="vm1.img"
# Name of bridge
export bridge_name="br-ovp"
# Domain name of VMs
export domain_vm1="test1_vm1"

do_test1()
{
	print_summary "Do test migration: non-shared storage, with --copy-storage-all"
        create_vm  'virtio' 
	get_vm_ip
        migration --copy-storage-all
}

do_test2()
{
	print_summary "Do test migration: non-shared storage, with --copy-storage-inc"
        create_vm  'virtio' 
	get_vm_ip
        migration --copy-storage-inc
}

start_test ()
{
        get_ip
        hosts_set
	load_kvm_kmod

	create_public_key
	prepare_image
	prepare_imgae_on_remote
	do_test1
	do_test2

        sleep 2
	clean
}

NON_SHARE_STORAGE=1
start_test
