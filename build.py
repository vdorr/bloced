

#TODO use as gedit plugin

import sys
import subprocess
import os
import tempfile
from functools import partial
import fnmatch
import re
from pprint import pprint
from collections import namedtuple

try :
	from serial.tools.list_ports import comports
except e :
	print("can not find appropriate version of pySerial")
	def comports() :
		return []
else :
	from serial import Serial
	from serial.serialutil import SerialException


def __run_external(args, workdir=None, redir=False) :
	redir_method = subprocess.PIPE if redir else None
	try :
		p = subprocess.Popen(args,
			stdout=redir_method,
			stderr=redir_method,
			cwd=os.getcwd() if workdir is None else workdir )
	except :
		return (False, None, tuple())
	else :
		(stdoutdata, stderrdata) = p.communicate()
		if p.returncode == 0 :
			return (True, p.returncode, (stdoutdata, stderrdata))
		else :
			return (False, p.returncode, (stdoutdata, stderrdata))


__src_exts = ( "*.c", "*.cpp" )
__hdr_exts = ( "*.h", "*.hpp" )

__re_src = re.compile("("+")|(".join([ fnmatch.translate(ln) for ln in __src_exts ])+")")
__re_hdr = re.compile("("+")|(".join([ fnmatch.translate(ln) for ln in __hdr_exts ])+")")


def __list_files(workdir, recurse, ignore=lambda fn: False) :
	sources = []
	inlude_dirs = []
	tree = os.walk(workdir)
	for root, dirs, files in tree if recurse else [ tree.next() ] :
		src_files = [ os.path.join(workdir, root, fn) for fn in files ]
		sources += [ fn for fn in src_files
			if __re_src.match(fn.lower()) and not ignore(fn) ]
		if any([ __re_hdr.match(fn) for fn in files ]) :
			inlude_dirs.append(os.path.join(workdir, root))
	return sources, inlude_dirs


def __read_lines(file_name) :
	try :
		f = open(file_name, "r")
		lines = f.readlines()
		f.close()
		return lines
	except :
		return None


def __read_ignore(fname) :
	lines = __read_lines(fname)
	if lines != None :
		return [ ln.strip() for ln in lines if ln.strip() ]


def __ignore_to_re(line) :
	ln = line.strip()
	return fnmatch.translate(ln) if ln and not ln[0] == "#" else None


def __parse_boards(boards_txt) :
	lines = __read_lines(boards_txt)
	if lines == None :
		return None
	valid = re.compile("\s*\w+\.\S+\s*=\s*\S+")
	board_info = {}
	for line in [ ln for ln in lines if valid.match(ln) ] :
		key, value = line.split("=")
		dot = key.index(".")
		board_name = key[0:dot].strip()
		if not board_name in board_info :
			board_info[board_name] = {}
		board_info[board_name][key[dot+1:].strip()] = value.strip()
	return board_info


def __port_test_read(port) :
#	print "__port_test_read:", port
	s = None
	try :
		s = Serial(port=port, timeout=0)
		s.read()
		s.close()
		s = None
	except SerialException :
		if s :
			s.close()
		return False
	return True


def get_ports(do_test_read=True) :
	ports = comports()
	if do_test_read :
		return [ p for p in ports if __port_test_read(p[0]) ]
	else :
		return ports


#TODO TODO TODO
BOARDS_TXT = "/usr/share/arduino/hardware/arduino/boards.txt"


def get_board_types() :
	return __parse_boards(BOARDS_TXT)


def __print_streams(*v) :
	print("".join([ f.decode() for f in v if f ]))


src_dir_t = namedtuple("src_dir", ["directory", "recurse"])

def build() :
	boards_txt = BOARDS_TXT
	ARDUINO_SRC_DIR = "/usr/share/arduino/hardware/arduino/cores/arduino"
	board = "uno"
	ignore_file = "amkignore"
	prog_port = "/dev/ttyACM0"
	workdir = os.getcwd()
	wdir_recurse = True
	dry_run = True #XXX XXX XXX XXX XXX 

	src_dirs = [
		src_dir_t(workdir, True),
		src_dir_t(ARDUINO_SRC_DIR, False)
	]


	ignores = __read_ignore(os.path.join(workdir, ignore_file))
#	pprint(ignores)
	ign_res = [ r for r in [ __ignore_to_re(ln) for ln in ignores ] if r ]
	re_ignore = re.compile("("+")|(".join(ign_res)+")")
	do_ignore = lambda fn: bool(ign_res) and bool(re_ignore.match(fn))

	sources, idirs = [], []
	for directory, recurse in src_dirs:
		src, loc_idirs = __list_files(directory, recurse,
			ignore=do_ignore)
		sources += src
		idirs += loc_idirs

##	ard_sources, ard_idirs = [], []
#	ard_sources, ard_idirs = __list_files(arduino_src_dir, False,
#		ignore=do_ignore)
#	pprint(ard_sources)

#	sources, loc_idirs = __list_files(workdir, wdir_recurse,
#		ignore=do_ignore)


#	pprint(sources)


	board_info = __parse_boards(boards_txt)

	mcu = board_info[board]["build.mcu"]
	f_cpu = board_info[board]["build.f_cpu"]
	flash_size = int(board_info[board]["upload.maximum_size"])
	prog_mcu = mcu.capitalize() #"m328p"

	print("%s (%s @ %iMHz), %i source file(s)" %
		(board_info[board]["name"], mcu, int(f_cpu[:-1])/1000000, len(sources)))

	run_gcc = partial(__run_external, workdir=workdir, redir=False)
	run = partial(__run_external, workdir=workdir, redir=True)

#	a_out_f = tempfile.NamedTemporaryFile()
#	a_hex_f = tempfile.NamedTemporaryFile()
#	a_out = a_out_f.name
#	a_hex = a_hex_f.name

	board_idirs = [ "/usr/lib/avr", "/usr/lib/avr/include",
		"/usr/lib/avr/util", "/usr/lib/avr/compat" ]
	a_out, a_hex = "a.out", "a.hex"
	i_dirs = [ "-I" + d for d in ( idirs + board_idirs ) ]
#""
	l_libs = []#[ "/usr/lib/avr/lib/libc.a" ]

	optimization = "-O0"

	gcc_args = i_dirs + l_libs + [ optimization, "-mmcu=" + mcu,
		"-DF_CPU=%s" % f_cpu, "-o", a_out ]
	gcc_args += sources

	success, _, streams = run_gcc(["avr-gcc"] + gcc_args)
	if success :
		stdoutdata, stderrdata = streams
		__print_streams("compiled", " ", stdoutdata, stderrdata)
	else :
		stdoutdata, stderrdata = streams
		__print_streams("failed to execute avr-gcc", " ",
			stdoutdata, stderrdata)
		sys.exit(10)

	success, rc, streams = run(["avr-size", a_out])
	if success :
		stdoutdata, _ = streams
		head, val = stdoutdata.decode().split(os.linesep)[0:2]
		sizes = dict(zip(head.split(), val.split()))
#TODO check against boards.txt
		print("memory usage: flash %iB, ram %iB" %
			(int(sizes["text"]),
			int(sizes["data"])+int(sizes["bss"])))
	else :
		print("failed to execute avr-size")
		sys.exit(20)

	success, _, __ = run(["avr-objcopy",
		"--strip-debug",
		"-j", ".text",
		"-j", ".data",
		"-O", "ihex", a_out, a_hex])
	if success :
		print("hex file created")
	else :
		print("failed to execute avr-objcopy")
		sys.exit(30)

#	sys.exit(0)#XXX XXX XXX XXX XXX

#	success, _, streams = run(["avrdude", "-q" ] +
##		["-n"] if dry_run else [] +
#		["-c"+"arduino",
#		"-P" + prog_port,
#		"-p" + prog_mcu,
#		"-Uflash:w:" + a_hex + ":i"])
	success, _, streams = run_gcc(["avrdude", "-q",# ] +
#		"-n", #] if dry_run else [] +
		"-c"+"arduino",
		"-P" + prog_port,
		"-p" + prog_mcu,
		"-Uflash:w:" + a_hex + ":i"])

	if success :
		print("succesfully uploaded")
	else :
		stdoutdata, stderrdata = streams
		print("failed to run avrdude '%s'" % stderrdata.decode())
		sys.exit(40)

# ----------------------------------------------------------------------------

if __name__ == "__main__" :
	build()

# ----------------------------------------------------------------------------

