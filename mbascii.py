
import serial
import struct
import os
from utils import here
#import time


def decode(buf) :
	assert(len(buf) >= 10)
	assert(buf[-1] == "\r")
	assert(not ((len(buf)-1) % 2))
	frame = "".join(chr((int(h, 16) << 4) + int(l, 16)) for h, l in zip(buf[0:-1:2], buf[1:-1:2]))
	if sum(ord(c) for c in frame) % 2 :
		print here(), "invalid lrc"
		return None
	addr, function = struct.unpack(">BB", frame[:2])
	if function == 0x10 :
		register, reg_cnt, byte_cnt = struct.unpack(">HHB", frame[2:7])
		assert(byte_cnt == 2 * reg_cnt)
		reg_values = struct.unpack(">" + reg_cnt * "H", frame[7:-1])
		print here(), addr, function, register, reg_cnt, byte_cnt, reg_values
		return addr, function, (register, reg_cnt, byte_cnt, reg_values)
	else :
		print here(), "unsupported function"
		return None


def main(port, baudrate, parity) :
	ser = serial.Serial()
	ser.port = port
	ser.baudrate = baudrate
	ser.parity = parity
	ser.open()

	frame = []
	while True :
		c = ser.read()#TODO use timeout to handle frame spacing
		if "0" <= c <= "9" or "A" <= c <= "F" or c == "\r" :
			frame.append(c)
		elif c == ":" :
			frame = []
		elif c == "\n" :
			decode(frame)
			frame = []
		else :
			frame = []
			print here(), "invalid char ", ord(c), "dec received"


if __name__ == "__main__" :
	port, baudrate, parity = "/dev/ttyACM0", 9600, "N"
	main(port, baudrate, parity)


