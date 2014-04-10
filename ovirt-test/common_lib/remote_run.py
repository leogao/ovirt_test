#!/usr/bin/env python
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
import commands

from optparse import OptionParser

root_password='root'

def parser_pre():

    """Parser pre parameters to decide which function should be run.
    Also get some the help info about this test.
    """
    usage = "usage: %prog -i $IP -f 'scp' -m $transmit_file \n     : %prog -i $IP -f 'ssh_run' -e $commands\n     : %prog -f 'console_run' -g $VM -e $commands \n"
    parser = OptionParser(usage = usage)
    parser.add_option('-i', '--ip',               type   = 'string',    dest = 'ip',               help = 'Get remote ip to scp file and run command')
    parser.add_option('-p', '--port',             type   = 'string',    dest = 'port',             help = 'Telnet remote login guest via ip and port')
    parser.add_option('-f', '--func',             type   = 'string',    dest = 'func',             help = 'Chose function which can be run')
    parser.add_option('-e', '--extra_parameter',  type   = 'string',    dest = 'extra_parameter',  help = 'Direct the extra parameters which used by func')
    parser.add_option('-m', '--transmit_file',    type   = 'string',    dest = 'transmit_file',    help = 'Transmited file between AP and station')
    parser.add_option('-l', '--download',  action = 'store_true',dest = 'download', default = False, help = 'download the file, default as upload')
    parser.add_option('-d', '--debug',     action = 'store_true',dest = 'debug',    default = False, help = 'Enable debug mode')
    parser.add_option('-g', '--guest',            type   = 'string',    dest = 'guest',            help = 'Login in a guest via guest name')
    (options, args) = parser.parse_args()

    global debug
    global download
    global guest
    global remote_ip
    global remote_port
    global func_run
    global extra_parameter
    global transmit_file


    if not (options.ip) and not (options.guest):
        print '\n%s\n' % (usage)
        sys.exit(1)
    else:
        remote_ip   = options.ip
        remote_port = options.port

    guest = options.guest
    debug      = options.debug
    download   = options.download
    func_run   = options.func
    extra_parameter  = options.extra_parameter
    transmit_file    = options.transmit_file

def print_debug(msg):
    if debug:
        print '\n[debug] ' + msg

def console_session_run(args_cmd='dmesg > dmesg_log'):
   
    """ Create remote run session on console. 
        %prog vm=$VM cmd=$CMD
        or 
        %prog port=$IP:$PORT cmd=$CMD
    eg. $>virsh console $VM 'and run $CMD'
    eg. $>telnet console $VM 'and run $CMD'
    """

    console_log = './guest_console.log'
    p_console = open(console_log,'a+w')
    F_ret = 0
    try:
        if guest: 
            run_cmd = 'virsh console %s' % (guest)
        else:
            run_cmd = 'telnet %s %s' % (remote_ip,remote_port)

        for i in range(1,10):
            console_session  = pexpect.spawn(run_cmd)
            console_session.logfile = p_console
            index = console_session.expect(['Escape character', pexpect.EOF], timeout=60)
            if index == 0:
                console_session.sendline('\n')
            index = console_session.expect(['login:', pexpect.EOF], timeout=60)
            if index == 0:
                console_session.sendline('root')
            index = console_session.expect(['Password:', pexpect.EOF], timeout=60)
            if index == 0:
                console_session.sendline('root')
                break
        console_session.logfile = sys.stdout
        console_session.sendline('%s ; echo echo_result=$?' % args_cmd)
        index = console_session.expect_exact(['echo_result=0', pexpect.EOF], timeout=100)
        if index != 0:
            F_ret += 1
    except Exception,e:
        print  'console_session_run (%s) -> unexpected issue: %s' % (args_cmd,e)
        F_ret += 1
    console_session.sendline('exit')
    console_session.terminate()
    p_console.close()
    if  F_ret != 0:
        print  'console run command(%s) failed' % (args_cmd)
        sys.exit(1)
    
def remote_session_run(args_cmd='ls'):
   
    """ Create remote run session. 
    eg. $>ssh root@ip 'commands'
    """

    F_ret = 0
    try:
        index = 0
        ssh_cmd = 'ssh -o "StrictHostKeyChecking=no" -o "GSSAPIAuthentication=no" '
        run_cmd = '%s root@%s \"%s\" ; echo \"echo_result=\"$?\"' % (ssh_cmd, remote_ip, args_cmd)

        warning = 'WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!'
        for i in range(1,10):
            remote_session  = pexpect.spawn(run_cmd)
            remote_session.logfile = sys.stdout
            index = remote_session.expect(['[Pp]assword:\s+', warning, pexpect.EOF], timeout=120)
            if index == 1:
                commands.getoutput('rm -rf ~/.ssh/known_hosts')
                remote_session.terminate()
            else:
                break
        if index == 0:
            remote_session.sendline('%s' % root_password)
        index = remote_session.expect_exact(['echo_result=0', pexpect.EOF], timeout=100)
        if index != 0:
            F_ret += 1
    except Exception,e:
        print  'remote_session_run (%s) -> unexpected issue: %s' % (args_cmd,e)
        F_ret += 1
    remote_session.terminate()
    if  F_ret != 0:
        print  'ssh run command(%s) failed' % (args_cmd)
        sys.exit(1)
    
def remote_session_scp(send_file='/bin/ls'):
   
    """ Create remote session copy file. 
        scp 100M file spend 200s, the spead is 0.5MB
    eg. $>scp xxx root@ip:/root/
    """

    F_ret = 0
    try:
        index = 0

        if download:
	    run_cmd = 'scp -o "StrictHostKeyChecking=no" -o "GSSAPIAuthentication=no" root@%s:%s .' % (remote_ip, send_file)
	else:
	    run_cmd = 'scp -o "StrictHostKeyChecking=no" -o "GSSAPIAuthentication=no" %s root@%s:/root/' % (send_file, remote_ip)

        print_debug(run_cmd)
        warning = 'WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!'
        for i in range(1,10):
            remote_session  = pexpect.spawn(run_cmd)
            remote_session.logfile = sys.stdout
            index = remote_session.expect(['[Pp]assword:\s+', warning, pexpect.EOF], timeout=120)
            if index == 1:
                commands.getoutput('rm -rf ~/.ssh/known_hosts')
                remote_session.terminate()
            else:
                break
        if index == 0:
            remote_session.sendline('%s' % root_password)
        index = remote_session.expect_exact(['100%', pexpect.EOF], timeout=1800)
        if index != 0:
            F_ret += 1
    except Exception,e:
        print  'remote_session_scp (%s) -> unexpected issue: %s' % (send_file,e)
        F_ret += 1
    remote_session.terminate()
    if  F_ret != 0:
        print  'scp larger file from server, transmit quality failed.'
        sys.exit(1)

def main():
    
    """ The main of this test case """
    parser_pre()

    if func_run == "scp":
        remote_session_scp(send_file = '%s' % transmit_file)
    if func_run == "ssh_run":
        remote_session_run(args_cmd = '%s' % extra_parameter)
    if func_run == "console_run":
        console_session_run(args_cmd = '%s' % extra_parameter)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
