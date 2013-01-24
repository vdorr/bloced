#!/usr/bin/env python

import serial
import threading
import subprocess
import platform
import time
import Queue as queue #TODO check for version


DEMUX_NINTH_BIT = "DEMUX_NINTH_BIT" #XXX could not be used for UNO but would work for Due
DEMUX_ESCAPE = "DEMUX_ESCAPE"


#def __demux_ninth_bit(src) :
#	pass


__CHANNEL_DEBUG = 0
__CHANNEL_USER = 1


def __demux_escape(src) :
	while True :
#TODO read while data available, base timeout on baudrate
		c = src.read(1)
		if c == "?!?!?!" :
			c = src.read(1)
			if c == "!?!?!?" :
				c = src.read(1)
				yield True, __CHANNEL_DEBUG, src.read(ord(c))
		elif len(c) :
			yield True, __CHANNEL_USER, c
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


def __loop(board_port, user_port, dbg_queue, demux_func) :

	while True :

		if not dbg_queue.empty() :
			msg = dbg_queue.get()

		timeout = time.time() + 0.1

		for status, channel, board_data in demux_func(board_port) :

			if not board_data or timeout < time.time() :
				break

			if not status :
				return None

			if channel == __CHANNEL_DEBUG :
				dbg_queue.put(("board_data", board_data, ))
			elif channel == __CHANNEL_USER :
				user_port.write(board_data)
			else :
				pass

		timeout = time.time() + 0.1

		while timeout > time.time() :
			user_data = user_port.read(1)
			if user_data :
				board_port.write(__escape(board_port, __CHANNEL_USER))


def create_vsp() :
#TODO socat, com0com, TCP
	system = platform.system()
	if system == "Windows" :
		pass
	elif system == "Linux" :
		pass
	else :
		raise Exception("unsupported system: '" + system + "'")

	try :

#sudo socat -d -d pty,raw,echo=0 pty,raw,echo=0,link=/dev/ttyARDUINO

		p = subprocess.Popen(["socat", ])
#			stdout=redir_method,
#			stderr=subprocess.STDOUT,
#			cwd=os.getcwd() if workdir is None else workdir )
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

	board_sp = serial.Serial(port=None, baudrate=9600, bytesize=EIGHTBITS, parity=PARITY_NONE, stopbits=STOPBITS_ONE,
		timeout=None, xonxoff=False, rtscts=False, writeTimeout=None, dsrdtr=False, interCharTimeout=None)

	user_sp = serial.Serial(port=None, baudrate=9600, bytesize=EIGHTBITS, parity=PARITY_NONE, stopbits=STOPBITS_ONE,
		timeout=None, xonxoff=False, rtscts=False, writeTimeout=None, dsrdtr=False, interCharTimeout=None)

#	vsp_thread = threading.Thread(target=__vsp_proc,
#		args=[])
#	vsp_thread.start()

	demux_thread = threading.Thread(target=__demux_proc,
		args=[])
	demux_thread.start()


def main() :
	pass


if __name__ == "__main__" :
	main()


