get_ip()
{
        Gateway=$(netstat -r | grep 'default' | awk '{ print $2}')
        Filter=$(echo $Gateway | awk -F. {'print $1"."$2"."$3'})
        IP=$(ifconfig | grep 'inet addr:'| grep -v '127.0.0.1' | cut -d: -f2 | awk '{ print $1}' | grep $Filter)
        echo "IP=$IP Gateway=$Gateway"
}

get_vm_ip()
{
	Gateway=$($REMOETE_RUN -f console_run -g $domain_vm1 -e 'netstat -r' \
		| grep 'default' | awk '{ print $2}')
	Filter=$(echo $Gateway | awk -F. {'print $1"."$2"."$3'})
	VM_IP=$($REMOETE_RUN -f console_run -g $domain_vm1 -e 'ifconfig' \
		| grep 'inet addr:'| grep -v '127.0.0.1' \
		| cut -d: -f2 | awk '{ print $1}' | grep $Filter)
	echo $VM_IP
}

hosts_set()
{
        print_steps "Setting two hosts nodes"
RE=${RE:-$REMOTE_HOST}
cat << EOF > /tmp/sethost.sh
#!/bin/bash
LO_NAME=\$1
RE_NAME=\$2
RE_FLAG=\$3

echo "127.0.0.1 localhost.localdomain           localhost" > /etc/hosts
echo "$IP       \$LO_NAME.wrs.com       \$LO_NAME" >> /etc/hosts
echo "$RE       \$RE_NAME.wrs.com       \$RE_NAME" >> /etc/hosts

if [[ \$# -gt 2 ]]; then
    echo "\$RE_NAME" > /etc/hostname
    hostname \$RE_NAME
else
    echo "\$LO_NAME" > /etc/hostname
    hostname \$LO_NAME
fi
EOF
        sleep 5
        bash /tmp/sethost.sh node1 node2
        $REMOETE_RUN -i $REMOTE_HOST -f scp -m /tmp/sethost.sh
        $REMOETE_RUN -i $REMOTE_HOST -f ssh_run -e "bash sethost.sh node1 node2 remote"
}


create_pool()
{
        print_steps "Create storage pool"

        # create export directory
        mkdir -p $EXPORTDIR
        chown vdsm:kvm $EXPORTDIR
        grep $EXPORTDIR /etc/exports
        if [[ $? -ne 0 ]]; then 
                echo "$EXPORTDIR   *(rw,sync,no_subtree_check,all_squash,anonuid=36,anongid=36)" >> /etc/exports
        fi
        service nfsserver restart
        NFSPID=$(pidof /usr/sbin/rpc.statd)
        [[ -z $NFSPID ]]
        check_status_1 "nfsserver restart failed."

        # gen pool xml
        pool_xml "$POOL_NAME" "$IP" "$EXPORTDIR"
        sleep 5

        # create local pool
        virsh pool-define /tmp/${POOL_NAME}.xml
	check_status "virsh pool-define ${POOL_NAME}.xml"
        virsh pool-start ${POOL_NAME}
	check_status "virsh pool-start ${POOL_NAME}"

        # create remote pool 
        $REMOETE_RUN -i $REMOTE_HOST -f scp -m /tmp/${POOL_NAME}.xml
        $REMOETE_RUN -i $REMOTE_HOST -f ssh_run -e "virsh pool-define ${POOL_NAME}.xml"
        $REMOETE_RUN -i $REMOTE_HOST -f ssh_run -e "virsh pool-start ${POOL_NAME}"
}

clean_pool()
{
        print_steps "Clean storage pool"

        # clean storage pool
        $REMOETE_RUN -i $REMOTE_HOST -f ssh_run -e "virsh pool-destroy ${POOL_NAME}"
        $REMOETE_RUN -i $REMOTE_HOST -f ssh_run -e "virsh pool-undefine ${POOL_NAME}"
        $REMOETE_RUN -i $REMOTE_HOST -f ssh_run -e "umount /data/images"

        virsh pool-destroy ${POOL_NAME}
        virsh pool-undefine ${POOL_NAME}
        umount /data/images
}

create_vm()
{
        print_steps "Create VM"
        # virtio/pdpk-vSwitch/passthrough
        VM_TYPE=$1
        if [[ $VM_TYPE == 'virtio' ]]; then 
                bridge_name='ovirtmgmt'
        elif [[ $VM_TYPE == 'vSwitch' ]]; then 
                bridge_name='br-ovp'
                br_ovp_ip='10.0.11.2'
                br_ovp_gw='10.0.11.1'
                vnet0_ip='10.0.11.50'

                ifconfig ${bridge_name} ${br_ovp_ip}
                CMD="ovs-vsctl add-br ${bridge_name}; ifconfig ${bridge_name} ${br_ovp_ip}"
                $REMOETE_RUN -i $REMOTE_HOST -f ssh_run -e "${CMD}"
        fi
        # gen vm xml
	create_xml "${domain_vm1}" "kvm" "512000" "${GUEST_MAC}" "${bridge_name}" "${path_kernel}/${guest_kernel}" "${path_img}/${guest_img_1}" "/tmp/${domain_vm1}.xml" ${vnet0_ip} ${br_ovp_ip} ${br_ovp_gw} 

        if [[ $VM_TYPE == 'virtio' ]]; then 
                sed -i "/<virtualport type='openvswitch'\/>/d" /tmp/${domain_vm1}.xml
        fi
	cat /tmp/${domain_vm1}.xml

        # create vm using xml
        virsh define /tmp/${domain_vm1}.xml
	check_status "define ${domain_vm1}"
        virsh start ${domain_vm1}
	check_status "start ${domain_vm1}"
}

clean ()
{
	echo ">>>>>>>>>>>>>>>>>>>>"
	echo "Clean system"
	echo "<<<<<<<<<<<<<<<<<<<<"
cat << EOF > /tmp/cleanhost.sh
#!/bin/bash
#Clean exist VMs before/after do testing.
all_vms=\$(virsh list --all | grep -v Id | grep -v "\---" | awk '{print \$2}')
for i in \${all_vms}; do
        virsh list --all | grep \$i | grep -q running
        if [ \$? -eq 0 ]; then
                echo "* Destroy \$i"
                virsh destroy \$i
                sleep 1
        fi
        virsh list --all | grep -q \$i
        if [ \$? -eq 0 ]; then
                echo "* Undefine \$i"
                virsh undefine \$i
                sleep 1
        fi
done
#Clean Bridge.
BR=\$(ovs-vsctl show | grep Bridge | awk '{print \$2}')
for i in \${BR}; do
        echo "* Delete br \$i"
        ovs-vsctl del-br \$i
        sleep 1
done
EOF
        bash /tmp/cleanhost.sh
        $REMOETE_RUN -i $REMOTE_HOST -f scp -m /tmp/cleanhost.sh
        $REMOETE_RUN -i $REMOTE_HOST -f ssh_run -e "bash cleanhost.sh"
	sleep 5
	echo "* Remove guest image from /var/lib/libvirt/images"
	rm -rvf /var/lib/libvirt/images/*
	echo "* Remove guest kernel from /var/lib/libvirt/boot"
	rm -rvf /var/lib/libvirt/boot/*
	echo "* Delete bridge ${bridge_name}"
	sleep 5
        [[ $NON_SHARE_STORAGE -ne 1 ]] && clean_pool
	exit $STATUS
}

prepare_image ()
{
	print_summary "Start prepare image"

	print_steps " copy guest kernel to ${path_kernel}"
	cp /boot/guest.kernel ${path_kernel}/${guest_kernel}
	check_status "copy guest kernel to ${path_kernel}"
        chmod 777 ${path_kernel}/${guest_kernel}

	print_steps " copy guest image to ${path_img}/${guest_img_1}"
	cp /boot/guest_raw.test ${path_img}/${guest_img_1}
	check_status " copy guest image to ${path_img}/${guest_img_1}"
        chmod 777 ${path_img}/${guest_img_1}

	print_steps " confirm libvirtd is running"
	ps -e | grep -q libvirt
	if [ $? -ne 0 ]; then
		/etc/init.d/libvirtd start
		check_status "libvirtd start"
	else
		pass_status
	fi

	print_steps " Create bridge ${bridge_name}"
	ovs-vsctl add-br ${bridge_name}
	check_status "create bridge"
}

prepare_imgae_on_remote()
{
        print_steps "Prepare images on remote machine"

        $REMOETE_RUN -i $REMOTE_HOST -f scp -m "${path_img}/${guest_kernel}"
        $REMOETE_RUN -i $REMOTE_HOST -f scp -m "${path_img}/${guest_img_1}"
        $REMOETE_RUN -i $REMOTE_HOST -f ssh_run -e "mv /root/{$guest_kernel,$guest_img_1} ${path_img}"
        $REMOETE_RUN -i $REMOTE_HOST -f ssh_run -e "chmod 777 ${path_img}/{$guest_kernel,$guest_img_1}"
}

pool_xml ()
{
#Generate the XML for the NFS storage pool.
POOL=$1
POOL_HOST=$2
POOL_HOST_PATH=$3

cat << EOF > /tmp/$POOL.xml
<pool type="netfs">
  <name>$POOL</name>
  <source>
    <host name='$POOL_HOST'/>
    <dir path='$POOL_HOST_PATH'/>
  </source>
  <target>
    <path>/var/lib/libvirt/images</path>
  </target>
</pool>
EOF
}

create_xml ()
{
domain=$1
type=$2
mem_size=$3
mac_addr=$4
bridge=$5
kernel=$6
image=$7
path=$8
ip_addr=$9
br_ip=${10}
gw=${11}

if [[ $# -gt 8 ]] ; then
        vnetip="${ip_addr}:${br_ip}:${gw}:255.255.255.0::eth0:off"
else
        vnetip="dhcp"
fi

cat << EOF > ${path}
<domain type='${type}'>
  <name>${domain}</name>
  <memory>${mem_size}</memory>
  <currentMemory>${mem_size}</currentMemory>
  <vcpu>1</vcpu>
  <os>
    <type arch='x86_64' machine='pc'>hvm</type>
    <boot dev='hd' />
    <kernel>${kernel}</kernel>
    <cmdline>console=ttyS0 root=/dev/hda rw ip=${vnetip}</cmdline>
  </os>
  <devices>
    <disk type='file' device='disk'>
      <driver name='qemu' type='raw' cache='none' io='threads'/>
      <source file='${image}' />
      <target dev='hda' bus='ide' />
    </disk>
    <interface type='bridge'>
      <mac address='${mac_addr}'/>
      <model type='virtio'/>
      <source bridge='${bridge}'/>
      <virtualport type='openvswitch'/>
      <address type='pci' domain='0x0000' bus='0x00' slot='0x03' function='0x0'/> 
    </interface>
    <graphics type='vnc' port='5900' autoport='yes' listen='0' keymap='en-us'>
      <listen type='address' address='0'/>
    </graphics>
    <serial type='pty'>
      <target port='0'/>
    </serial>
    <console type='pty'>
      <target type='serial' port='0'/>
    </console>
  </devices>
</domain>
EOF
}

migration()
{
        print_steps "Do VM live migration testing"

	# --copy-storage-all or --copy-storage-inc to do migration.
	COPY_STORAGE_TYPE=$1

        GUEST_DMESG=guest_dmesg.log
        GUEST_MOUNT="/media/guest"

        # local to remote
        virsh migrate --live --p2p --verbose $COPY_STORAGE_TYPE $domain_vm1 qemu+tcp://$REMOTE_HOST/system
        check_status "Migrate${domain_vm1}"
        sleep 5

	if [[ $NON_SHARE_STORAGE -eq 1 ]]; then
		$REMOETE_RUN -i $VM_IP -f ssh_run -e "dmesg > $GUEST_DMESG"
		mkdir $GUEST_MOUNT/root
		$REMOETE_RUN -i $VM_IP -f scp -m "~/$GUEST_DMESG" -l
		mv $GUEST_DMESG $GUEST_MOUNT/root/
		$REMOETE_RUN -i $REMOTE_HOST -f ssh_run -e "virsh destroy $domain_vm1"
	        virsh undefine $domain_vm1
	else
		# remote to local
		$REMOETE_RUN -i $REMOTE_HOST -f ssh_run -e "virsh migrate --live --p2p --verbose $domain_vm1 qemu+tcp://$IP/system"

		# check vm's dmesg
		$REMOETE_RUN -f console_run -g $domain_vm1 -e "dmesg > $GUEST_DMESG"

		sleep 10
		mkdir -p $GUEST_MOUNT
		mount $path_img/$guest_img_1 $GUEST_MOUNT
	fi

        if [[ -s $GUEST_MOUNT/root/$GUEST_DMESG ]]; then 
            print_steps "Check guest VM dmesg after migration"
            cp $GUEST_MOUNT/root/$GUEST_DMESG .
            umount $GUEST_MOUNT
            cat $GUEST_DMESG  
            cat $GUEST_DMESG | grep -Ei 'error|Call Trace:' | grep -v 'ACPI Error' 
            check_status_1 "Check guest ${domain_vm1} dmesg info"
        else
            umount $GUEST_MOUNT
        fi
}
