#!/usr/bin/env python

import serial
import threading
import subprocess
import platform
import time
from sys import version_info
if version_info.major == 3 :
	import queue
else :
	import Queue as queue
from binascii import hexlify

from utils import here
#from StringIO import StringIO
#import sys


#DEMUX_NINTH_BIT = "DEMUX_NINTH_BIT" # could not be used for UNO but would work for Due
DEMUX_ESCAPE = "DEMUX_ESCAPE"


__CHANNEL_DEBUG = 0
__CHANNEL_USER = 1

__ESCAPE_CHAR = "\xff"


def demux_escape(src, default_channel=0, wait_for_sync=True) :

#	print here(), default_channel, wait_for_sync, src.inWaiting()

	channel = None if wait_for_sync else default_channel

	rx_cnt = 0

	while True :
#TODO read while data available, base timeout on baudrate
		c = src.read(1)
		rx_cnt += len(c)

#		if 0 and len(c) :
#			print here(), rx_cnt, hex(ord(c)) if len(c) else "(empty)"

		if wait_for_sync and (channel is None) and (c != __ESCAPE_CHAR) :
#			print here(), hex(ord(c)) if len(c) else "(empty)"
			yield True, None, "" #everything ok, just waiting for sync
			continue

##		print(here(), c)
		if c == __ESCAPE_CHAR :
#			print here()
			while True :
				c = ""
				while not len(c) :
					c = src.read(1)
					rx_cnt += len(c)
#				print here(), hex(ord(c))
				if c != __ESCAPE_CHAR :
					channel = ord(c)
					c = ""
					print(here(), rx_cnt, "current channel set to:", channel)
				break
#				if c != __ESCAPE_CHAR :
#					channel = ord(c)
#					print here(), rx_cnt, "current channel set to:", channel
#					break
#				else :
#					continue
		elif len(c) :
#			print(here(), rx_cnt, channel, hex(ord(c)) if len(c) else "(empty)")
			yield True, channel, c
		else :
			yield True, None, "" #everything ok, just got no data


def __escape(data, channel) :
	return __ESCAPE_CHAR + chr(channel) + data


def loop(brd_port_name, user_port, dbg_port, demux_func, control_queue,
		status_queue, wait_for_sync=True) :
	"""
wait_for_sync - if True, drop all data that arrive before first control symbol
	"""

	while True :

		board_port = None
		while board_port is None :
			try :
				board_port = serial.Serial(port=brd_port_name,
					baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE,
					stopbits=serial.STOPBITS_ONE, timeout=0.01, xonxoff=False,
					rtscts=False, writeTimeout=None, dsrdtr=False, interCharTimeout=None)
				print(here())
			except serial.SerialException :
				board_port = None
				if not control_queue.empty() :
					(cmd, ) = control_queue.get_nowait()
					if cmd == "detach" :
						print(here())
						return None
					else :
						print(here(), '"', cmd, '"', "UNKNOWN COMMAND")
				time.sleep(0.5)

		try :
			status_queue.put(("demux_entry", ))
			rc = __inner_loop(board_port, user_port, dbg_port, demux_func, control_queue,
				status_queue, wait_for_sync=wait_for_sync)
			if rc == "detach" :
				print(here())
				return None
		except serial.SerialException as e : #Exception as e :
#TODO distinguish termination command and loss of port
#			status_queue.put(("serial_exception", e, ))
			print(here(), e)
#			raise e

#			board_port.flush()
		board_port.close()
		board_port = None
		print(here(), "port closed!")

		status_queue.put(("demux_exit", ))


def __inner_loop(board_port, user_port, dbg_port, demux_func, control_queue,
		status_queue, wait_for_sync=True) :

	port_reader = demux_func(board_port, wait_for_sync=wait_for_sync)

	while True :

		if not control_queue.empty() :
			(cmd, ) = control_queue.get_nowait()
			if cmd == "detach" :
				return "detach"
			else :
				print(here(), '"', cmd, '"', "UNKNOWN COMMAND")

		timeout = time.time() + 0.1

		for status, channel, board_data in port_reader :

			if not board_data or timeout < time.time() :
				break

			if not status :
				return "detach"

#			print here(), status, channel#, board_data

			if channel == __CHANNEL_DEBUG :
				dbg_port.write(board_data)
			elif channel == __CHANNEL_USER :
				user_port.write(board_data)
			else :
				raise Exception("{} invalid channel number '{}'".format(here(), channel))

		timeout = time.time() + 0.05
		while timeout > time.time() :
			user_data = user_port.read(1)
			if len(user_data) :
				print here(), "writing to board!"
				board_port.write(__escape(user_data, __CHANNEL_USER))

		timeout = time.time() + 0.05
		while timeout > time.time() :
			pass
#			dbg_data = dbg_port.read(1)
#			if len(dbg_data) :
#				print here(), "writing to board!"
#				board_port.write(__escape(dbg_data, __CHANNEL_DEBUG))


def destroy_vsp(instance) :
	system = platform.system()
	if system == "Windows" :
		raise Exception("unsupported system: '" + system + "'")#TODO
	elif system == "Linux" :
		print(here(), "killing socat")
		instance.kill()
	else :
		raise Exception("unsupported system: '" + system + "'")
	print(here())


class GWVSP(object) :


	def get_port_names(self) :
		return self.__ports


	def close(self) :
		self.__close_function(self.__instance)


	def __init__(self, instance, ports, close_function) :
		self.__instance = instance
		self.__ports = ports
		self.__close_function = close_function


def create_vsp(system=None) :
	"""
	return three tuple of vsp instance and two port names
	"""
#TODO socat, com0com, TCP
#TODO on Linux create symlink in /dev/ to /tmp/ during install
	system = platform.system() if system is None else system
	if system == "Windows" :
		raise Exception("unsupported system: '" + system + "'")#TODO
	elif system == "Linux" :
		instance, port_a, port_b = create_socat_pty_vsp_pair()
		return GWVSP(instance, (port_a, port_b), destroy_vsp)
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
		print(here(), e)
		raise

	return p, ptys[0], ptys[1]


#TODO
class DebugPort(object) :

	def read(self, n) :
		return n*"."

	def write(self, data) :
		self.rx_cnt += len(data)
#		print here(), hexlify(data)
#		if len(data) and self.rx_cnt % 30 == 0 :
#			print here(), str(self.rx_cnt) + " bytes received"
		pass

	def __init__(self) :
		self.rx_cnt = 0


def check_user_port_config(user_port_type, user_port_path, user_port_settings) :
	type_ok = user_port_type in set(["VSP_AUTO"])#, "UART", "TCP", "UDP", "RFC2217"])
	path_ok = True #TODO check user_port_path
	settings_ok = True #TODO check user_port_settings
	return type_ok and path_ok and settings_ok


class Gateway(object) :


	def destroy(self) :
		print(here())
		self.detach()
		if not self.__vsp_instance is None :
			self.__vsp_instance.close()
			self.__vsp_instance = None


	def detach(self) :
		print(here())
		if self.__demux_thread is None :
			print(here())
			return None
		print(here())
		self.__control_queue.put(("detach", ))
		print(here())
#		while not self.__control_queue.empty() :
#			self.__control_queue.get_nowait()
#		print(here())
		self.__demux_thread.join(10)
		print(here())
		if self.__demux_thread.is_alive() :
			print(here())
			raise Exception(here() + " failed to kill demux")
		self.__demux_thread = None


	def attach(self) :
		return self.attach_to(self.__board_port)


	def __start_demux(self) :
		assert(self.__demux_thread is None)
		brd_port_name = self.__board_port
		usr_port_name = self.__get_internal_port()

		user_sp = serial.Serial(port=usr_port_name,
			baudrate=9600,
			bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
			timeout=0.01,
			xonxoff=False, rtscts=False, writeTimeout=None, dsrdtr=False, interCharTimeout=None)

		dbg_port = self.__dbg_port_instance
		demux_func = demux_escape

		self.__demux_thread = threading.Thread(target=loop,
			name="gateway thread {}".format(time.time()),
			args=[brd_port_name, user_sp, dbg_port, demux_func, self.__control_queue, self.__status_queue])

		self.__demux_thread.start()


	def attach_to(self, board_port) :
		need_reattach = self.__board_port != board_port
		print(here(), board_port, need_reattach, self.__demux_thread is None)
		self.__board_port = board_port
		if need_reattach or self.__demux_thread is None :
			if not self.__demux_thread is None :
				print(here())
				self.detach()
				print(here())
			print(here())
			self.__start_demux()
		print(here())


	def configure_user_port(self, user_port_type, user_port_path, user_port_settings) :
#TODO handle case with automatically generated user_port (socat)
#TODO mind different types of user_port (TCP)

		assert(check_user_port_config(user_port_type, user_port_path, user_port_settings))

		new_config = (user_port_type, user_port_path, user_port_settings)
		need_new_vsp = self.__user_port != new_config
		self.__user_port = new_config
		if need_new_vsp :
			print(here(), new_config)
			if not self.__vsp_instance is None :
				self.__vsp_instance.close()
				self.__vsp_instance = None
			self.__vsp_instance = create_vsp()
			print(here())
#			self.__dummy_events = [ "vsp_created" ]
			self.__has_events = True


	def get_board_port_state(self) :
		return self.__board_port_state


	def get_board_port_ready(self) :
		return self.get_board_port_state() == "attached"


	def get_user_port(self) :
		"""
		returns path to user port
		"""

		if not self.__vsp_instance is None :
			_, outer = self.__vsp_instance.get_port_names()
			return outer

		return None


	def __get_internal_port(self) :
		inner, _ = self.__vsp_instance.get_port_names()
		return inner


	def poll_events(self) :
#		print here()
		self.__poll_status_queue()
#		events = list(self.__dummy_events)
#		self.__dummy_events = []
		has_events = self.__has_events
		self.__has_events = False
		return has_events


	def __set_board_port_state(self, new_state) :
		if new_state != self.__board_port_state :
			self.__board_port_state = new_state
			self.__has_events = True


	def __poll_status_queue(self) :

		while not self.__status_queue.empty() :
			data = self.__status_queue.get_nowait()
			msg = data[0]
			if msg == "demux_exit" :
				self.__set_board_port_state("detached")
			elif msg == "demux_entry" :
				self.__set_board_port_state("attached")
			else :
				print(here(), data)


	def __init__(self, dbg_port_instance=None) :#, create_own_timer=False) :

		print(here(), "gw instance created")

#		if create_own_timer :
#			assert(False)

		self.__dbg_port_instance = DebugPort() if dbg_port_instance is None else dbg_port_instance
		self.__board_port = None
		self.__user_port = None
		self.__vsp_instance = None
#		self.__dummy_events = []
		self.__has_events = False
		self.__demux_thread = None
		self.__board_port_state = "unknown"#"unknown", "attached", "detached"
		self.__control_queue = queue.Queue()
		self.__status_queue = queue.Queue()


#TODO check socat availability!!!



