#!/usr/bin/env python
#
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#
# author: Wei Gao
# history: created on Dec 27, 2013
# 

import sys
sys.path.append('../common_lib/')
from ovirt_engine_api import *

class test( data_center ):
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
        self.test_dict['DATACENTERS'].append(('NfsDataCenter','nfs'))
        self.test_dict['DATACENTERS'].append(('IscsiDataCenter','iscsi'))
        self.test_dict['DATACENTERS'].append(('FibreChannelDataCenter','fcp'))
        self.test_dict['DATACENTERS'].append(('LocalHostDataCenter','localfs'))
        self.test_dict['DATACENTERS'].append(('PosixFSDataCenter','posixfs'))

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
                name = self.test_dict['DATACENTERS'][i][0]
                type = self.test_dict['DATACENTERS'][i][1]
                self.print_summary('New a %s type data center' % (type))
                if self.new_data_center(name,type) == False:
                    print 'New a %s type data center failed' % (type)
                    return False
            if self.disconnect() != None:
                print 'Disconnect ovirt-engine failed' % (name)
                return False

        except Exception as e:
            print 'Failed to create Data Center):\n%s' % (str(e))
            return False

    def clean( self ):
        '''Destructor for test.'''
        try:
            self.__connect__()
            length = len(self.ovirt_dict['DATACENTERS'])
            for i in range(0,length):
                name = self.test_dict['DATACENTERS'][i][0]
                type = self.test_dict['DATACENTERS'][i][1]
                self.print_summary('Remove (%s)' % (name))
                if self.delete_data_center(name) != False:
                    print 'Remove data center(%s) failed' % (name)
                    return False
            if self.disconnect() != None:
                print 'Disconnect ovirt-engine failed' % (name)
                return False

        except Exception as e:
            print 'Failed to clean Data Center:\n%s' % (str(e))
            return False

def main():
    ''' Input engine ip'''
    EG_IP = sys.argv[1]
    caserun = test(EG_IP)
    if caserun.execute() == False:
        sys.exit(1)
    if caserun.clean() == False:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
