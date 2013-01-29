#!/usr/bin/env python

import serial
import threading
import subprocess
import platform
import time
import Queue as queue #TODO check for version
from utils import here
#from StringIO import StringIO
import sys


DEMUX_NINTH_BIT = "DEMUX_NINTH_BIT" #XXX could not be used for UNO but would work for Due
DEMUX_ESCAPE = "DEMUX_ESCAPE"


#def __demux_ninth_bit(src) :
#	pass


__CHANNEL_DEBUG = 0
__CHANNEL_USER = 1

__ESCAPE_CHAR = "\xff"


def __demux_escape(src, default_channel=0, wait_for_sync=True) :

	channel = None if wait_for_sync else default_channel

	while True :
#TODO read while data available, base timeout on baudrate
		c = src.read(1)

		if wait_for_sync and (channel is None) and (c != __ESCAPE_CHAR) :
			yield True, None, "" #everything ok, just waiting for sync

##		print here(), c
		if c == __ESCAPE_CHAR :
			c = src.read(1)
			if c != __ESCAPE_CHAR :
				channel = ord(c)
				print here(), channel
				continue

		if len(c) :
			yield True, channel, c
		else :
			yield True, None, "" #everything ok, just got no data

		


__DEMUX_FUNCTIONS = {
#	DEMUX_NINTH_BIT : (__demux_ninth_bit, ),
	DEMUX_ESCAPE : (__demux_escape, ),
}


def __escape(data, channel) :
	return "" + data + ""


#def __unescape(data) :
#	return channel, data


#TODO commands: disable_escaping, fix_channel, close_channel, open_channel


def __loop(board_port, user_port, dbg_queue, demux_func, wait_for_sync=True) :
	"""
wait_for_sync - if True, drop all data that arrive before first control symbol
	"""

	port_reader = demux_func(board_port)

	while True :

		if not dbg_queue.empty() :
			msg = dbg_queue.get()

		timeout = time.time() + 0.1

		for status, channel, board_data in port_reader :

			if not board_data or timeout < time.time() :
				break

			if not status :
				return None

			if channel == __CHANNEL_DEBUG :
				#dbg_queue.put(("board_data", board_data, ))
				print here(), board_data
			elif channel == __CHANNEL_USER :
				print here(), board_data
				#user_port.write(board_data)
			else :
				print here()
				pass

		timeout = time.time() + 0.1

		while timeout > time.time() :
			user_data = user_port.read(1)
			if user_data :
#				board_port.write(__escape(board_port, __CHANNEL_USER))
				pass


def create_vsp() :
#TODO socat, com0com, TCP
#TODO on Linux create symlink in /dev/ to /tmp/ during install
	system = platform.system()
	if system == "Windows" :
		pass
	elif system == "Linux" :
		pass
	else :
		raise Exception("unsupported system: '" + system + "'")

#	my_stdout = StringIO()

	try :

#sudo socat -d -d pty,raw,echo=0 pty,raw,echo=0,link=/dev/ttyARDUINO

		p = subprocess.Popen(["socat", "-d", "-d", "pty,raw,echo=0", "pty,raw,echo=0" ],
			stdout=subprocess.PIPE,
			stderr=subprocess.STDOUT,
#			cwd=os.getcwd() if workdir is None else workdir
		)

		s = ""
		while True :
			s += p.stdout.read(1)
			if s[-1] == "\n" :
				print s
				s = ""

	except Exception as e:
		print e


def __vsp_proc():
	pass


def __demux_proc():
	pass


def run_gateway(demux_method, brd_port_name, usr_port_name) :
	#vsp thread
	#demux thread
#serial.Serial
#    __init__(port=None, baudrate=9600, bytesize=EIGHTBITS, parity=PARITY_NONE, stopbits=STOPBITS_ONE,
#timeout=None, xonxoff=False, rtscts=False, writeTimeout=None, dsrdtr=False, interCharTimeout=None)

	board_sp = serial.Serial(port=brd_port_name,
		baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
		timeout=0,
		xonxoff=False, rtscts=False, writeTimeout=None, dsrdtr=False, interCharTimeout=None)

	user_sp = serial.Serial(port=usr_port_name,
		baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
		timeout=0,
		xonxoff=False, rtscts=False, writeTimeout=None, dsrdtr=False, interCharTimeout=None)

#	vsp_thread = threading.Thread(target=__vsp_proc,
#		args=[])
#	vsp_thread.start()

#	demux_thread = threading.Thread(target=__demux_proc,
#		args=[])
#	demux_thread.start()

	dbg_queue = queue.Queue()
	(demux_func, ) = __DEMUX_FUNCTIONS[demux_method]

	print here()
	__loop(board_sp, user_sp, dbg_queue, demux_func, wait_for_sync=True)


def main() :

	create_vsp()
	sys.exit()

	run_gateway(DEMUX_ESCAPE, "/dev/ttyACM0", "/dev/pts/9")

	pass


if __name__ == "__main__" :
	main()


