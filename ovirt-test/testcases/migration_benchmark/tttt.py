#!/usr/bin/env python

def run_func():
    try:
        bash_session  = pexpect.spawn('bash')
	bash_session.logfile = sys.stdout
        index = bash_session.expect(['root@.*#', pexpect.EOF], timeout=60)
        if index == 0:
	    cmd="python migrate_net_downtime.py client 10.0.1.3 2000 360 > downtime.elem & PID=$(echo $!); echo 'pid='$PID"
            bash_session.sendline(cmd)
        index = bash_session.expect(['pid=', pexpect.EOF], timeout=60)
        if index == 0:
            bash_session.sendline('kill -s INT %1')
        index = bash_session.expect(['KeyboardInterrupt', pexpect.EOF], timeout=60)

        if index == 0:
            bash_session.sendline('kill -s INT %1')
        index = bash_session.expect(['KeyboardInterrupt', pexpect.EOF], timeout=60)
        if index == 0:
            print  'ok ok '
    except Exception,e:
        print  'bash_session_run -> unexpected issue:' % (e)
    bash_session.sendline('exit')
    bash_session.terminate()
