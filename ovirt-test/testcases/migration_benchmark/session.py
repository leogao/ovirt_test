#!/usr/bin/env python
#
# Copyright 2014 Wind River Systems, Inc.
#
# The right to copy, distribute, modify, or otherwise make use
# of this software may be licensed only pursuant to the terms
# of an applicable Wind River license agreement.
#
# author: Wei Gao
# history: created on Jan 19, 2014
# 

import pexpect
import sys
import commands

class session():
    """Build a session for remote login 
    and continue run commands on the target machine. """ 

    def __init__(self, Target_ip, Logfile = sys.stdout, Password = 'root'):
        '''Do initiation'''
        try:
            index = 0
            pre_ssh  = 'ssh -o "StrictHostKeyChecking=no" -o "GSSAPIAuthentication=no"'
            comb_cmd = '%s root@%s' % (pre_ssh, Target_ip)
            warning = 'WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!'
            for i in range(1,10):
                self.session = pexpect.spawn(comb_cmd)
                self.session.logfile = Logfile
                index = self.session.expect(['[Pp]assword:\s+', warning, pexpect.EOF], timeout=120)
                if index == 1:
                    commands.getoutput('rm -rf ~/.ssh/known_hosts')
                    self.session.terminate()
                else:
                    break
            if index == 0:
                self.session.sendline('%s' % Password)
            self.session.sendline('pwd')
            self.session.expect_exact(['/root', pexpect.EOF], timeout=120)
        except Exception,e:
            print  'Build session failed, unexpected issue: %s' % (e)
            sys.exit(1)

    def destroy(self):
        '''Destroy this session'''
        self.session.terminate()

    def run_cmd(self, Cmd, Expect):
        '''Run command on the remote manchine 
        and got expected value'''
        try:
            self.session.sendline(Cmd)
            index = self.session.expect([Expect, pexpect.EOF], timeout=120)
        except Exception,e:
            print  'Run commandon(%s) failed, unexpected issue: %s' % (Cmd,e)
            sys.exit(1)
