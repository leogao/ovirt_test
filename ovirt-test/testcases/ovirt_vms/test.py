#!/usr/bin/env python
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#
# author: Wei Gao
# history: created on Dec 27, 2013
# 

import time
import sys
sys.path.append('../common_lib/')
from ovirt_engine_api import *

class test( virtualMachine ):
    """ Test for data-center inherit data_center."""
    def __init__( self, EG_IP, NODES, STORAGES ):
        '''Constructor for test.'''
        self.test_dict = {}
        self.test_dict['URL'] = 'https://%s:443/api' % (EG_IP)
        self.test_dict['VERSION'] = params.Version(major='3', minor='2')
        self.test_dict['CA_FILE'] = "/etc/pki/ovirt-engine/ca.pem"
        self.test_dict['USERINFOS'] = []
        self.test_dict['USERINFOS'].append(('admin@internal','admin'))
        self.test_dict['CONNECTION'] = False
        self.test_dict['DATACENTERS'] = []

        self.test_dict['DATACENTERS'].append(('Nfs','nfs'))
        #self.test_dict['DATACENTERS'].append(('Iscsi','iscsi'))
        #self.test_dict['DATACENTERS'].append(('FibreChannel','fcp'))
        #self.test_dict['DATACENTERS'].append(('LocalHost','localfs'))
        #self.test_dict['DATACENTERS'].append(('PosixFS','posixfs'))

        self.test_dict['CLUSTERS'] = []
        CPU_TYPE = 'Intel Conroe Family'
        self.test_dict['CLUSTERS'].append(('Conroe',CPU_TYPE))
        CPU_TYPE = 'Intel Nehalem Family'
        self.test_dict['CLUSTERS'].append(('Nehalem',CPU_TYPE))
        CPU_TYPE = 'Intel Penryn Family'
        self.test_dict['CLUSTERS'].append(('Penryn',CPU_TYPE))
        CPU_TYPE = 'Intel Westmere Family'
        self.test_dict['CLUSTERS'].append(('Westmere',CPU_TYPE))
        CPU_TYPE = 'Intel SandyBridge Family'
        self.test_dict['CLUSTERS'].append(('SandyBridge',CPU_TYPE))
        CPU_TYPE = 'Intel Haswell'
        self.test_dict['CLUSTERS'].append(('Haswell',CPU_TYPE))

        self.test_dict['HOSTS'] = []
        length = len(NODES.split(','))
        for i in range(0,length):
            host = ['node%d' % i]
            host.extend(list(NODES.split(',')[i].split(':')))
            self.test_dict['HOSTS'].append(tuple(host))

        self.test_dict['STORAGES'] = []
        length = len(STORAGES.split(','))
        for i in range(0,length):
            type = list(STORAGES.split(',')[i].split(':'))[0]
            storage = ['%s_domain' % type]
            storage.extend(list(STORAGES.split(',')[i].split(':')))
            self.test_dict['STORAGES'].append(tuple(storage))

        self.test_dict['VMS'] = []
        self.test_dict['VMS'].append('vm1','server')
        self.test_dict['VMS'].append('vm2','desktop')

        self.ovirt_dict = {}
        super(test, self).__init__(self.test_dict)

    def __connect__( self ):
        '''Connect ovirt for test.'''
        try:
            self.print_summary('Create a session to ovirt-engine')
            self.connect_engine()
            self.printInstanceInfo()

            self.print_summary('Check ovirt-engine connection')
            if self.ovirt_dict['CONNECTION'] == False :
                print 'Connect ovirt-engine failed \n'
                return False
        except Exception as e:
            print 'Failed to connect ovirt-engine:\n%s' % (str(e))
            return False

    def pre_cluster_host( self, dc_name ):
        '''Do New Storage domain testing '''
        length = len(self.test_dict['HOSTS'])
        for i in range(0,length):
            hs_name  = self.test_dict['HOSTS'][i][0]
            hs_addr  = self.test_dict['HOSTS'][i][1]
            cllength = len(self.test_dict['CLUSTERS'])
            for j in range(0,cllength):
                if self.test_dict['CLUSTERS'][j][1] != self.test_dict['HOSTS'][i][2]:
                    continue
                else:
                    cl_name  = self.test_dict['CLUSTERS'][j][0]
                    cl_type  = self.test_dict['CLUSTERS'][j][1]
                    break
            if j + 1 >= cllength:
                print 'Can not found suit cluster in list' % (cl_name)
                return False
            if self.new_cluster(cl_name,cl_type,dc_name) == False:
                print 'New a %s type cluster in %s failed' % (cl_type,dc_name)
                return False
            self.print_summary('New host in cluster %s' % (cl_name))
            if self.new_host(hs_name,hs_addr,cl_name) == False:
                print 'New a host in cluster %s failed' % (cl_name)
                return False

    def clean_cluster_host( self, dc_name ):
        '''Do New Storage domain testing '''
        length = len(self.test_dict['HOSTS'])
        for i in range(0,length):
            hs_name  = self.test_dict['HOSTS'][i][0]
            hs_addr  = self.test_dict['HOSTS'][i][1]
            cllength = len(self.test_dict['CLUSTERS'])
            for j in range(0,cllength):
                if self.test_dict['CLUSTERS'][j][1] != self.test_dict['HOSTS'][i][2]:
                    continue
                else:
                    cl_name  = self.test_dict['CLUSTERS'][j][0]
                    cl_type  = self.test_dict['CLUSTERS'][j][1]
                    break
            if j + 1 >= cllength:
                print 'Can not found suit cluster in list' % (cl_name)
                return False

            if self.delete_host(hs_name,hs_addr,cl_name) == False:
                print 'Delete a host in cluster %s failed' % (cl_name)
                return False
            time.sleep(2)
            if self.delete_cluster(cl_name,cl_type,dc_name) == False:
                print 'Delete a %s type cluster in %s failed' % (cl_type,dc_name)
                return False

    def vm_test( self, dc_name, cl_name ):
        '''VM testing '''
        if self.pre_storage(dc_name) == False:
            print 'Prepare a storage domains, in data-center(%s) failed' % (dc_name)
            return False

        length = len(self.test_dict['VMS'])
        for i in range(0,length):
            vm_name  = self.test_dict['VMS'][i][0]
            vm_type  = self.test_dict['VMS'][i][1]
            if self.new_vm(vm_name,vm_type,cl_name) == False:
                print 'New a VM (%s) failed' % (vm_name)
                return False
            vd_name = '_'.join((vm_name,'vdisk'))
            if self.do_add_disk(vd_name,dm_name,vm_name) == False:
                print 'New a vdisk on VM (%s) failed' % (vm_name)
                return False

    def pre_storage( self, dc_name ):
        '''Do New Storage domain testing '''
        if self.pre_cluster_host(dc_name) == False:
            print 'Prepare a cluster, host in data-center(%s) failed' % (dc_name)
            return False

        length = len(self.test_dict['STORAGES'])
        for i in range(0,length):
            dm_name  = self.test_dict['STORAGES'][i][0]
            dm_type  = self.test_dict['STORAGES'][i][1]
            dm_addr  = self.test_dict['STORAGES'][i][2]
            dm_path  = self.test_dict['STORAGES'][i][3]
            if self.new_storage_domain(dm_name,dm_type,dm_addr,dm_path,dc_name) == False:
                print 'New a storage domain(%s) failed' % (dm_name)
                return False

        '''
        length = len(self.test_dict['STORAGES'])
        for i in range(0,length):
            dm_name  = self.test_dict['STORAGES'][i][0]
            if self.judge_master_domain(dm_name) == True:
                print 'Master domain(%s) can NOT be removed' % (dm_name)
                continue
            if self.delete_storage_domain(dc_name, dm_name) == False:
                print 'Delete Storage domain(%s) failed' % (dm_name)
                return False

        if self.clean_cluster_host(dc_name) == False:
            print 'Clean a cluster, host in data-center(%s) failed' % (dc_name)
            return False
        '''

    def execute( self ):
        '''Constructor for test.'''
        try:
            self.__connect__()
            length = len(self.test_dict['DATACENTERS'])
            for i in range(0,length):
                dc_name = self.test_dict['DATACENTERS'][i][0]
                dc_type = self.test_dict['DATACENTERS'][i][1]
                self.print_summary('New data center(%s)' % (dc_name))
                if self.new_data_center(dc_name,dc_type) == False:
                    print 'New a %s type data center failed' % (dc_type)
                    return False
                self.print_summary('Continue adding host')
                if self.storage_test(dc_name) == False:
                    print 'Storage domain testing in data-center(%s) failed' % (dc_name)
                    return False

                time.sleep(3)
                if self.delete_data_center(dc_name) == False:
                    print 'Remove data center(%s) failed' % (dc_name)
                    return False
            if self.disconnect() != None:
                print 'Disconnect ovirt-engine failed' % (name)
        except Exception as e:
            print 'Failed to do storage domains test\n%s' % (str(e))
            return False

def main():
    ''' Input engine ip
        Input nodes info "ip1:cputype ip2:cputype" '''
    EG_IP    = sys.argv[1]
    NODES    = sys.argv[2]
    STORAGES = sys.argv[3]
    caserun = test(EG_IP, NODES, STORAGES)
    if caserun.execute() == False:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
