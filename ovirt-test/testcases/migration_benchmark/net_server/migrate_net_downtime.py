#!/usr/bin/python
#
# This tool measures the maximum network downtime.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# Usage (migrate from nodeA to nodeB):
#       Log on the VM, start the server on the background and exit:
#          migrate_net_downtime.py server <vm_ip> &
#       Start the client on nodeB:
#          migrate_net_downtime.py client <vm_ip> <downtime_threshold_ms> <runtime_threshold_sec>
#
# Where:
#       <downtime_threshold_ms> is in microsecond.
#       <runtime_threshold_sec> is in seconds
#
# Notes:
#       The client outputs updated maximum downtime and exits either if it
#       exceeds the downtime threshold or if the tool runs longer than the
#       runtime threshold.
#

import SocketServer
import socket, sys, datetime, time
from decimal import Decimal

def gettimestamp():
		return str(datetime.datetime.now().time())

def getdowntime(start, end):
	# Parse string with this format 15:06:34.021147 to get hour, minute
	# second and microsecond.
	h_start = start[0:start.find(':')]
	h_start_remain = start[start.find(':')+1:len(start)]
	m_start = h_start_remain[0:h_start_remain.find(':')]
	m_start_remain = h_start_remain[h_start_remain.find(':')+1:len(h_start_remain)]
	s_start = m_start_remain[0:m_start_remain.find('.')]
	us_start = m_start_remain[m_start_remain.find('.')+1:len(m_start_remain)]
	# Microseconds total of start timestamp
	start_us = (int(h_start)*3600 + int(m_start)*60 + int(s_start))*1000000+int(us_start)

	# Similar with end migration time
	h_end = end[0:end.find(':')]
	h_end_remain = end[end.find(':')+1:len(end)]
	m_end = h_end_remain[0:h_end_remain.find(':')]
	m_end_remain = h_end_remain[h_end_remain.find(':')+1:len(h_end_remain)]
	s_end = m_end_remain[0:m_end_remain.find('.')]
	us_end = m_end_remain[m_end_remain.find('.')+1:len(m_end_remain)]
	# Microseconds total of end timestamp
	if int(h_end) < int(h_start):
		print 'Migration end time roll over'
		end_us = ((int(h_end)+24)*3600 + int(m_end)*60 + int(s_end))*1000000+int(us_end)
	else:
		end_us = (int(h_end)*3600 + int(m_end)*60 + int(s_end))*1000000+int(us_end)
	# Return downtime in microsecond
	return (end_us - start_us)

class server_handler(SocketServer.BaseRequestHandler):
	def handle(self):
		data = self.request[0].strip()
		socket = self.request[1]
		# print(data+" from %s" % self.client_address[0])
		socket.sendto(data.upper(), self.client_address)

BUF_MAX  = 1024
PORT = 5454
# Server ping period
PING_PERIOD_UP = 0.002
PING_PERIOD_DOWN = 0.001
MIN_RUNTIME = 20
# Duration to determine the server response
SOC_TIMEOUT = 0.005

# For migration from nodeA to nodeB, server is run on VM and client on nodeB
if len(sys.argv) == 3 and sys.argv[1] == 'server':
	ip_address = sys.argv[2]
	server = SocketServer.UDPServer((ip_address, PORT), server_handler)
	server.serve_forever()
elif len(sys.argv) == 5 and sys.argv[1] == 'client':
	max_delay, idx_send, eth_down = 0, 0, 0
	last_ts = ""
	ip_address = sys.argv[2]
	delay_threshold = int(sys.argv[3])
	# Ping period is 2 ms normally, so limit minimum runtime to 20s to have
	# enough pings for benchmark.
	if (int(sys.argv[4]) >= MIN_RUNTIME):
		exit_time = int(time.time()) + int(sys.argv[4])
	else:
		print 'Runtime threshold should be at least %d seconds' %MIN_RUNTIME
		sys.exit(1)

	soc = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	soc.settimeout(SOC_TIMEOUT)
	print 'Client socket name is', soc.getsockname()
	print 'Network delay threshold: '+sys.argv[3]+' ms'
	print 'Maximum runtime period: '+sys.argv[4]+' second(s)'
	while True:
		# Check how long the tool has run and exit if necessary.
		if int(time.time()) == exit_time:
			print 'Exit: '+sys.argv[4]+' seconds have elapsed.'
			sys.exit(0)
		# Normally, the VM is pinged every 2ms. During the network downtime,
		# the VM is pinged every 1ms to detect the active network as early
		# as possible.
		if eth_down == 0:
			time.sleep(PING_PERIOD_UP)
		else:
			time.sleep(PING_PERIOD_DOWN)
		try:
			idx_send += 1
			soc.sendto(str(idx_send), (ip_address,PORT))
		except KeyboardInterrupt:
			print 'KeyboardInterrupt'
			sys.exit(1)
		except:
			# The server on the VM does not receive because of network
			# downtime. Try to send again
			eth_down = 1
		else:
			try:
				data_client, serverAddress = soc.recvfrom(BUF_MAX)
			except KeyboardInterrupt:
				print 'KeyboardInterrupt'
				sys.exit(1)
			except:
				# No response from the server on the VM due to network
				# downtime. Go back to ping the server again.
				eth_down = 1
			else:
				eth_down = 0
				if len(last_ts) != 0:
					current_ts = gettimestamp()
					delta_us = getdowntime(last_ts, current_ts)
					# This downtime includes the delay between 2 pings, so
					# subtract the delay to get the real downtime.
					delta_ms = Decimal(delta_us)/Decimal(1000) - Decimal(1000*PING_PERIOD_UP)
					if delta_ms > max_delay:
						print 'Updated maximum network delay: '+str(delta_ms)+' ms'
						max_delay = delta_ms
						if max_delay > delay_threshold:
							print '\nMaximum delay exceeds %d' %delay_threshold+' ms'
							soc.close()
							sys.exit(1)
				last_ts = gettimestamp()
else:
	print 'Usage:'
	print '    '+sys.argv[0]+' server <vm_ip>'
	print '    '+sys.argv[0]+' client <vm_ip> <downtime_threshold_ms> <runtime_threshold_min>'
