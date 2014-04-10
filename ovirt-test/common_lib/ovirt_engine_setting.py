#!/usr/bin/env python
#
# Copyright 2013 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#
# author: Wei Gao
# history: created on Nov 5, 2013
# 


import pexpect
import sys
import os
import time
import commands

from optparse import OptionParser

def parser_pre():

    """Parser pre parameters to decide which function should be run.
    Also get some the help info about this test.
    """
    usage = "usage: %prog -f $function -w $firewall [-d $domain -p $http_port -P $https_port -m $mode -s $storage -t $db_type -i $iso -w $firewall -v $vdsm -D] \n"
    parser = OptionParser(usage = usage)
    parser.add_option('-f', '--func',             type   = 'string',    dest = 'func',             help = 'Chose function which can be run')
    parser.add_option('-d', '--domain',           type   = 'string',    dest = 'domain',           help = 'Host fully qualified domain name')
    parser.add_option('-p', '--http_port',        type   = 'string',    dest = 'http_port',        help = 'Get http port  eg: HTTP Port [80]')
    parser.add_option('-P', '--https_port',       type   = 'string',    dest = 'https_port',       help = 'Get https port eg: HTTPS Port [443]')
    parser.add_option('-m', '--mode',             type   = 'string',    dest = 'mode',             help = 'The engine can be configured three different application modes [virt|gluster|both]')
    parser.add_option('-s', '--storage',          type   = 'string',    dest = 'storage',          help = 'storage type you will be using  [NFS|FC|ISCSI|POSIXFS]')
    parser.add_option('-t', '--db_type',          type   = 'string',    dest = 'db_type',          help = 'Enter DB type for installation [remote|local] ')
    parser.add_option('-i', '--iso',              type   = 'string',    dest = 'iso',              help = 'ISO domain path eg: /export/local/iso ')
    parser.add_option('-w', '--firewall',         type   = 'string',    dest = 'firewall',         help = 'Which firewall do you wish to configure? [None]')
    parser.add_option('-v', '--vdsm',             type   = 'string',    dest = 'vdsm',             help = 'Which firewall do you wish to configure? [None]')
    parser.add_option('-D', '--debug',     action = 'store_true',dest = 'debug',  default = False, help = 'Enable debug mode')
    (options, args) = parser.parse_args()

    global debug
    global func_run
    global http_port
    global https_port
    global domain_name
    global admin_password 
    global engine_mode
    global storage_type
    global db_type
    global iso_flag
    global iso_path
    global firewall
    global vdsm

    if (options.func != 'engine_cleanup'):
	if not (options.firewall):
	    print '\n%s\n' % (usage)
	    sys.exit(1)
    if not (options.http_port):
        http_port =  80
    if not (options.https_port):
        https_port = 443
    if (options.mode):
        engine_mode = options.mode
    else:
        engine_mode = 'both'

    if (options.storage):
        storage_type = options.storage
    else:
        storage_type = 'NFS' 
    if (options.db_type):
    	db_type = options.db_type
    else:
    	db_type = 'local' 
    if (options.firewall):
        firewall = options.firewall
    else:
        firewall = 'None'
    if (options.iso):
        iso_path = options.iso
        iso_flag = 'yes'
    else:
        iso_flag = 'no' 
    if (options.vdsm):
        vdsm = options.vdsm
    else:
        vdsm = 'no' 

    debug       = options.debug
    func_run    = options.func
    domain_name = options.domain
    admin_password = 'admin' 

def print_debug(msg):
    if debug:
        print '\n[debug] ' + msg

def engine_setup(args_cmd='engine-setup'):
   
    """ Create remote run session. 
    eg. $>ssh root@ip 'commands'
    """

    F_ret = 0
    try:
        index = 0
        for i in range(1,5):
            session  = pexpect.spawn(args_cmd)
            session.logfile = sys.stdout
	    msg1 = 'Would you like to proceed'
            msg2 = 'Would you like to stop the ovirt-engine service'
            msg3 = 'Do you wish to override current httpd configuration and restart the service'
            index = session.expect([msg1, msg2, msg3, pexpect.EOF], timeout=30)
	    print (index)
            if index == 0 or index == 1:
                session.sendline('yes')
                index = session.expect([msg3, pexpect.EOF], timeout=30)
                if index == 0:
                    session.sendline('yes')
	    elif index == 2:
                session.sendline('yes')
            else: 
                sys.exit(1)
                break
            for j in range(1,10):
                index = session.expect(['HTTP Port', pexpect.EOF], timeout=30)
                if index == 0:
                    session.sendline('%s' % str(http_port))
                    index = session.expect(['HTTPS Port', 'already open by httpd', pexpect.EOF], timeout=30)
                    if index == 0:
                        if index == 0:
                            session.sendline('%s' % str(https_port))
                        break 
                    elif index == 1:
                        '''wait for httpd stopped'''
                        time.sleep(3)
                        continue 

            msg = 'Host fully qualified domain name. Note: this name should be fully resolvable'
            index = session.expect([msg, pexpect.EOF], timeout=30)
            if index == 0:
                if domain_name != None:
                    session.sendline('%s' % domain_name)
                else:
                    session.sendline('\r')

            msg = 'Enter a password for an internal oVirt Engine administrator user' 
            index = session.expect([msg, pexpect.EOF], timeout=30)
            if index == 0:
		session.sendline('%s' % admin_password)
            index = session.expect(['Confirm password', pexpect.EOF], timeout=30)
            if index == 0:
		session.sendline('%s' % admin_password)

            msg = 'Organization Name for the Certificate'
            index = session.expect([msg, pexpect.EOF], timeout=30)
            if index == 0:
                session.sendline('ovirt-test')

            msg = 'The engine can be configured to present the UI' 
            index = session.expect([msg, pexpect.EOF], timeout=30)
            if index == 0:
                session.sendline('%s' % engine_mode)

            sd_msg = 'The default storage type you will be using'
            db_msg = 'Enter DB type for installation'
            index = session.expect([sd_msg, db_msg, pexpect.EOF], timeout=30)
            if index == 0:
                session.sendline('%s' % storage_type)
                index = session.expect([db_msg, pexpect.EOF], timeout=30)
                if index == 0:
                    session.sendline('%s' % db_type)
            elif index == 1:
                session.sendline('%s' % db_type)

            msg = 'Enter a password for a local oVirt Engine DB admin user'
            index = session.expect([msg, pexpect.EOF], timeout=30)
            if index == 0:
		session.sendline('%s' % admin_password)
            index = session.expect(['Confirm password', pexpect.EOF], timeout=30)
            if index == 0:
		session.sendline('%s' % admin_password)

            iso_msg = 'Configure NFS share on this server to be used as an ISO Domain'
            firewall_msg = 'Which firewall do you wish to configure'
            index = session.expect([iso_msg, firewall_msg, pexpect.EOF], timeout=30)
            if index == 0:
                session.sendline('%s' % iso_flag)
                index = session.expect(['ISO domain path', firewall_msg, pexpect.EOF], timeout=30)
                if index == 0:
                    if iso_path != None:
                        session.sendline('%s' % iso_path)
                    else:
                        session.sendline(' ')
                    index = session.expect([firewall_msg, pexpect.EOF], timeout=30)
                    if index == 0:
                        session.sendline('%s' % firewall)
                elif index == 1:
                    session.sendline('%s' % firewall)
            elif index == 1:
                session.sendline('%s' % firewall)

            do_msg = 'Proceed with the configuration listed above'
            vdsm_msg = 'Configure VDSM on this host'
            index = session.expect([vdsm_msg, do_msg, pexpect.EOF], timeout=30)
            if index == 0:
                session.sendline('%s' % vdsm)
                index = session.expect([do_msg, pexpect.EOF], timeout=30)
                if index == 0:
                    session.sendline('yes')
                    break
            elif index == 1:
                session.sendline('yes')
                break
        index = session.expect(['Installation completed successfully', pexpect.EOF], timeout=300)
        if index != 0:
            F_ret += 1
    except Exception,e:
        print  'session (%s) -> unexpected issue: %s' % (args_cmd,e)
        F_ret += 1
    session.terminate()
    return F_ret
    
def engine_cleanup(args_cmd='engine-cleanup'):
   
    """ Create remote run session. 
    eg. $>ssh root@ip 'commands'
    """

    F_ret = 0
    try:
        index = 0
        session  = pexpect.spawn(args_cmd)
        session.logfile = sys.stdout
        msg1 = 'Would you like to proceed'
        msg2 = 'Password for user postgres'
        msg3 = 'Password for user engine'
        index = session.expect([msg1, pexpect.EOF], timeout=30)
        if index == 0:
            session.sendline('yes')
            for i in range(1,10):
                index = session.expect([msg2, msg3, pexpect.EOF], timeout=30)
                if index == 0 or index == 1:
                    session.sendline('%s' % admin_password)
                index = session.expect([msg2, msg3, 'Cleanup finished successfully', pexpect.EOF], timeout=30)
                if index == 0 or index == 1:
                    session.sendline('%s' % admin_password)
                elif index == 2:
                    break
        for i in range(1,10):
	    index = session.expect(['log available at', 'DB Backup available at', pexpect.EOF], timeout=30)
	    if index == 1:
		break
    except Exception,e:
        print  'session (%s) -> unexpected issue: %s' % (args_cmd,e)
        F_ret += 1
    session.terminate()
    return F_ret
    
def main():
    
    """ The main of this test case """
    parser_pre()

    if func_run == "engine_setup":
        RET = engine_setup()
    elif func_run == "engine_cleanup":
        RET = engine_cleanup()
    else:
        sys.exit(1)
    sys.exit(RET )
     
if __name__ == '__main__':
    try:
        main()
    except pexpect.EOF:
        fail()
    except pexpect.TIMEOUT:
        fail()
