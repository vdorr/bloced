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
			c = ""
			while not len(c) :
				c = src.read(1)
			if c != __ESCAPE_CHAR :
				channel = ord(c)
#				print here(), channel
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
#				print here(), board_data
				pass
			elif channel == __CHANNEL_USER :
#				print here(), board_data
				user_port.write(board_data)
			else :
				print here()
				pass

		timeout = time.time() + 0.1

		while timeout > time.time() :
			user_data = user_port.read(1)
			if user_data :
				board_port.write(__escape(user_data, __CHANNEL_USER))
				pass


def destroy_vsp(instance) :
	system = platform.system()
	if system == "Windows" :
		raise Exception("unsupported system: '" + system + "'")#TODO
	elif system == "Linux" :
		pass
#TODO
	raise Exception("unsupported system: '" + system + "'")



def create_vsp() :
#TODO socat, com0com, TCP
#TODO on Linux create symlink in /dev/ to /tmp/ during install
	system = platform.system()
	if system == "Windows" :
		raise Exception("unsupported system: '" + system + "'")#TODO
	elif system == "Linux" :
		return create_socat_pty_vsp_pair()
	raise Exception("unsupported system: '" + system + "'")


def create_socat_pty_vsp_pair() :
	try :

#sudo socat -d -d pty,raw,echo=0 pty,raw,echo=0,link=/dev/ttyARDUINO

		p = subprocess.Popen(["socat", "-d", "-d", "pty,raw,echo=0", "pty,raw,echo=0" ],
			stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

		s = ""
		ptys = []
		while len(ptys) != 2 :
			s += p.stdout.read(1)
			if s[-1] == "\n" :
				tokens = s.split("PTY is")
				if len(tokens) == 2 :
					ptys.append(tokens[1].strip())
				s = ""
#		print here(), ptys

	except Exception as e:
#		print e
		raise

	return p, ptys[0], ptys[1]


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
		timeout=0.01,
		xonxoff=False, rtscts=False, writeTimeout=None, dsrdtr=False, interCharTimeout=None)

	user_sp = serial.Serial(port=usr_port_name,
		baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
		timeout=0.01,
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

	vsp_instance, inner_port_name, outer_port_name = create_vsp() #XXX maybe should return instance to abstract channel type (serial/socket)
	print here(), inner_port_name, "user port:", outer_port_name
#	time.sleep(1000)
#	sys.exit()

	run_gateway(DEMUX_ESCAPE, "/dev/ttyACM0", inner_port_name)

	destroy_vsp(vsp_instance)


if __name__ == "__main__" :
	main()

"""
#define UART_MUX_CHANNELS  2
//uint8_t uart_mux_state[UART_MUX_CHANNELS];
uint8_t uart_mux_current_channel = 0xff;//channels allowd 0..254

int uart_put_byte_escaped(uint8_t channel, uint8_t c)
{
  if ( uart_mux_current_channel != channel )
  {
    uart_mux_current_channel = channel;
    Serial.write((uint8_t)0xff);
    Serial.write((uint8_t)channel);
  }
  int bytes_sent = 0;
  if ( 0xff == c )
  {
    Serial.write((uint8_t)0xff);
    bytes_sent += 1;
  }
  Serial.write((uint8_t)c);
  bytes_sent += 1;
  return bytes_sent;
}

int uart_send_from_buffer(uint8_t channel, uint8_t* buffer, unsigned count)
{
  int bytes_sent = 0;
  for ( unsigned i = 0; i < count; i++)
  {
    uart_put_byte_escaped(channel, buffer[i]);
  }
  return 0;//TODO need proper error handling
}

int uart_receive_to_buffer(uint8_t channel, uint8_t* buffer, unsigned max_count)
{
}

void init_uart_mux()
{
  //memset(uart_mux_state, 0, sizeof(uart_mux_state));
  uart_mux_current_channel = -1;
}

uint8_t txt0[] = "sdfghjkl";
uint8_t txt1[] = "mnbvcx";

void loop()
{
  uart_send_from_buffer(1,txt0, sizeof(txt0));
  delay(100);
  uart_send_from_buffer(0,txt1, sizeof(txt1));
  delay(100);
}

void setup()
{
  init_uart_mux();
  txt0[3] = 0xff;
  Serial.begin(9600);
}
"""
