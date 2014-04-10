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

class test( cluster ):
    """ Test for data-center inherit data_center.
    """
    def __init__ ( self, EG_IP ):
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
        self.test_dict['DATACENTERS'].append(('Iscsi','iscsi'))
        self.test_dict['DATACENTERS'].append(('FibreChannel','fcp'))
        self.test_dict['DATACENTERS'].append(('LocalHost','localfs'))
        self.test_dict['DATACENTERS'].append(('PosixFS','posixfs'))

        self.test_dict['CLUSTERS'] = []
        CPU_TYPE = 'Intel Nehalem Family'
        self.test_dict['CLUSTERS'].append(('Nehalem',CPU_TYPE))
        CPU_TYPE = 'Intel Conroe Family'
        self.test_dict['CLUSTERS'].append(('Conroe',CPU_TYPE))
        CPU_TYPE = 'Intel Penryn Family'
        self.test_dict['CLUSTERS'].append(('Penryn',CPU_TYPE))
        CPU_TYPE = 'Intel Westmere Family'
        self.test_dict['CLUSTERS'].append(('Westmere',CPU_TYPE))
        CPU_TYPE = 'Intel SandyBridge Family'
        self.test_dict['CLUSTERS'].append(('SandyBridge',CPU_TYPE))
        CPU_TYPE = 'Intel Haswell'
        self.test_dict['CLUSTERS'].append(('Haswell',CPU_TYPE))

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

    def execute( self ):
        '''Constructor for test.'''
        try:
            self.__connect__()
            length = len(self.test_dict['DATACENTERS'])
            for i in range(0,length):
                dc_name = self.test_dict['DATACENTERS'][i][0]
                dc_type = self.test_dict['DATACENTERS'][i][1]
                self.print_summary('New data center(%s)' % (dc_name))
                if self.new_data_center(dc_name,dc_type) != False:
                    print 'New a %s type data center ok' % (dc_type)
                    length = len(self.test_dict['CLUSTERS'])
                    for i in range(0,length):
                        cl_name = self.test_dict['CLUSTERS'][i][0]
                        cl_type = self.test_dict['CLUSTERS'][i][1]
                        self.print_summary('New cluster(%s) in %s' % (cl_name,dc_name))
                        if self.new_cluster(cl_name,cl_type,dc_name) == False:
                            print 'New a %s type cluster in %s failed' % (cl_type,dc_name)
                            return False

                        time.sleep(3)
                        self.print_summary('Delete cluster(%s) in %s' % (cl_name,dc_name))
                        if self.delete_cluster(cl_name,cl_type,dc_name) == False:
                            print 'Delete a %s type cluster in %s failed' % (cl_type,dc_name)
                            return False

                time.sleep(3)
                if self.delete_data_center(dc_name) == False:
                    print 'Remove data center(%s) failed' % (dc_name)
                    return False

            if self.disconnect() != None:
                print 'Disconnect ovirt-engine failed' % (name)
                return False

        except Exception as e:
            print 'Failed to do cluster test:\n%s' % (str(e))
            return False

def main():
    ''' Input engine ip'''
    EG_IP = sys.argv[1]
    caserun = test(EG_IP)
    if caserun.execute() == False:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
