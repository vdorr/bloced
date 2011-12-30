

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
from itertools import islice

try :
	from serial.tools.list_ports import comports
	from serial import Serial
	from serial.serialutil import SerialException
except e :
	print("can not find appropriate version of pySerial")
	def comports() :
		return []
#TODO fake rest of imports


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


def __re_from_glob_list(globs) :
	expr = "(" + ")|(".join([ fnmatch.translate(ln) for ln in globs ]) + ")"
	return re.compile(expr)


__src_exts = ( "*.c", "*.cpp" )
__hdr_exts = ( "*.h", "*.hpp" )

__re_src = __re_from_glob_list(__src_exts)
__re_hdr = __re_from_glob_list(__hdr_exts)


def list_resources(workdir, recurse, ignore=lambda fn: False,
		re_src=__re_src, re_hdr=__re_hdr) :
	sources = []
	include_dirs = []
	tree = os.walk(workdir)
	src_total, idir_total = 0, 0
	for root, dirs, files in tree if recurse else islice(tree, 1) :
		src_files = [ os.path.join(workdir, root, fn) for fn in files if re_src.match(fn) ]
		src_total += len(src_files)
		sources += [ fn for fn in src_files if not ignore(fn) ]
		if any([ re_hdr.match(fn) for fn in files ]) :
			++idir_total
			idir = os.path.join(workdir, root)
			if not ignore(idir) :
				include_dirs.append(idir)
	return sources, include_dirs, src_total, idir_total


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


def get_board_types() :
	return __parse_boards(BOARDS_TXT)


def __print_streams(*v) :
	print("".join([ str(f) for f in v if f ]))
#	print("".join([ f.decode("utf8", "replace") for f in v if f ]))


src_dir_t = namedtuple("src_dir", ["directory", "recurse"])


#TODO temp file mode
def build_source(board, source,
		aux_src_dirs = [],
		boards_txt = None,
		board_db = {},
		ignore_file = "amkignore",
		prog_port = None,
		prog_driver = "avrdude", # or "dfu-programmer"
		prog_adapter = "arduino", #None for dfu-programmer
		optimization = "-Os",
		verbose = False,
		skip_programming = False,
		dry_run = False,
		blob_stream=None) :
	"""
blob_stream
	writeble file-like object, of not None, hex file will be written to this file
	"""
	return (0, )

def build(board, workdir,
		wdir_recurse = True,
		aux_src_dirs = [],
		boards_txt = None,
		board_db = {},
		ignore_file = "amkignore",
		prog_port = None,
		prog_driver = "avrdude", # or "dfu-programmer"
		prog_adapter = "arduino", #None for dfu-programmer
		optimization = "-Os",
		verbose = False,
		skip_programming = False,
		dry_run = False ) :
	"""
boards_txt
	path to arduino-style boards.txt
	at least this or board_db must be supplied
skip_programming
	compile, create hex, but do not start programming driver
dry_run
	as above, but use dry run of driver (avrdude -n)
ignore_file
	path to file with ignored file, applied to all source dirs, including auxiliary
	one glob per line, lines starting with # are skipped
aux_src_dirs
	list of 2-tuples (str, bool) (directory, recurse)
board_db
	appended to data from boards.txt, usefull if there is no boards.txt
	{ "uno" : {
		"name":"uno board",
		"build.mcu" : "atmega328p", #for avrdude/dfu-programmer
		"build.f_cpu" : "16000000L",
		"upload.maximum_size" : "32000" } }
	"""

	board_info = board_db
	if boards_txt :
		boards_txt_data = __parse_boards(boards_txt)
		if not boards_txt_data :
			print("failed to read boards info from '%s'" % boards_txt)
		else :
			board_info.update(boards_txt_data)
	if not board_info :
		print("got no board informations, quitting")
		return (200,)

	src_dirs = [ src_dir_t(workdir, True) ] + aux_src_dirs

	do_ignore = lambda fn: False
	if ignore_file :
		ignores = __read_ignore(os.path.join(workdir, ignore_file))
		if ignores != None :
#			pprint(ignores)
			ign_res = [ r for r in [ __ignore_to_re(ln) for ln in ignores ] if r ]
			re_ignore = re.compile("("+")|(".join(ign_res)+")")
			do_ignore = lambda fn: bool(ign_res) and bool(re_ignore.match(fn))
		else :
			print("error reading ignore file '%s'" % ignore_file)

	sources, idirs = [], []
	src_total, idir_total = 0, 0
	for directory, recurse in src_dirs:
		try :
			src, loc_idirs, srccnt, idircnt = list_resources(
				directory, recurse, ignore=do_ignore)
			src_total += srccnt
			idir_total += idircnt
		except StopIteration :
			print("can not access '%s'" % directory)
		else :
			sources += src
			idirs += loc_idirs
#	pprint(sources)

	mcu = board_info[board]["build.mcu"]
	f_cpu = board_info[board]["build.f_cpu"]
	flash_size = int(board_info[board]["upload.maximum_size"])
	prog_mcu = mcu.capitalize()

	print("%s (%s @ %iMHz), %i(%i) source files, %i(%i) include directories" %
		(board_info[board]["name"], mcu, int(f_cpu[:-1])/1000000,
		len(sources), src_total, len(idirs), idir_total))

	run = partial(__run_external, workdir=workdir, redir=True)
	run_loud = partial(__run_external, workdir=workdir, redir=False)
#	run_loud = run

#	a_out_f = tempfile.NamedTemporaryFile()
#	a_hex_f = tempfile.NamedTemporaryFile()
#	a_out = a_out_f.name
#	a_hex = a_hex_f.name

	board_idirs = [ "/usr/lib/avr", "/usr/lib/avr/include",
		"/usr/lib/avr/util", "/usr/lib/avr/compat" ]
	a_out, a_hex = "a.out", "a.hex"
	i_dirs = [ "-I" + d for d in ( idirs + board_idirs ) ]
	l_libs = []#[ "/usr/lib/avr/lib/libc.a" ]

	gcc_args = i_dirs + l_libs + [ optimization, "-mmcu=" + mcu,
		"-DF_CPU=%s" % f_cpu, "-o", a_out ]
	gcc_args += sources

	success, _, streams = run_loud(["avr-gcc"] + gcc_args)
	if success :
		stdoutdata, stderrdata = streams
		__print_streams("compiled", " ", stdoutdata, stderrdata)
	else :
		stdoutdata, stderrdata = streams
		__print_streams("failed to execute avr-gcc", " ",
			stdoutdata, stderrdata)
		return (10, )

	success, rc, streams = run(["avr-size", a_out])
	if success :
		stdoutdata, _ = streams
		head, val = stdoutdata.decode().split(os.linesep)[0:2]
		sizes = dict(zip(head.split(), val.split()))
		total_flash = int(sizes["text"])
		total_sram = int(sizes["data"])+int(sizes["bss"])
		print("memory usage: flash %iB (%.1f%%), ram %iB" %
			(total_flash, total_flash*100.0/flash_size, total_sram))
		if total_flash > flash_size :
			print("input file is bigger than target flash!")
	else :
		print("failed to execute avr-size")
		return (20, )

	success, _, __ = run(["avr-objcopy",
		"--strip-debug",
		"-j", ".text",
		"-j", ".data",
		"-O", "ihex", a_out, a_hex])
	if success :
		print("hex file created")
	else :
		print("failed to execute avr-objcopy")
		return (30, )

	if not skip_programming :
		if prog_driver == "avrdude" :
			if not prog_port :
				print("avrdude programmer port not set!, quitting")
				return (400, )
			success, _, streams = run(["avrdude", "-q", ] +
				(["-n", ] if dry_run else []) +
				["-c"+prog_adapter,
				"-P" + prog_port,
				"-p" + prog_mcu,
				"-Uflash:w:" + a_hex + ":i"])
			if success :
				print("succesfully uploaded")
			else :
				stdoutdata, stderrdata = streams
				print("failed to run avrdude '%s'" % stderrdata.decode())
				return (40, )
		elif prog_driver == "dfu-programmer" :
			if not dry_run :
				success, _, streams = run(["dfu-programmer", prog_mcu, "erase"])
				if not success :
					print("failed to erase chip")
					return (601, )
				success, _, streams = run(["dfu-programmer",
					prog_mcu, "flash", a_hex])
				if not success :
					print("failed to write flash")
					return (602, )
			if dry_run :
				success, _, streams = run(["dfu-programmer", prog_mcu, "reset"])
				if not success :
					print("failed to reset mcu")
					return (603, )
			else :
				success, _, streams = run(["dfu-programmer", prog_mcu, "start"])
				if not success :
					print("failed to start mcu")
					return (604, )
			return (40, )
		else :
			print("unknown programmer driver")
			return (40, )
	return (0, )

# ----------------------------------------------------------------------------


#TODO TODO TODO guess it, somehow
BOARDS_TXT = "/usr/share/arduino/hardware/arduino/boards.txt"


if __name__ == "__main__" :
	AUX_SRC_DIR = "/usr/share/arduino/hardware/arduino/cores/arduino"
	rc, = build("uno", os.getcwd(),
		wdir_recurse = True,
		aux_src_dirs = [ src_dir_t(AUX_SRC_DIR, False) ],
		boards_txt = BOARDS_TXT,
		ignore_file = "amkignore",
		prog_port = "/dev/ttyACM0",
		prog_driver = "avrdude", # or "dfu-programmer"
		prog_adapter = "arduino", #None for dfu-programmer
		optimization = "-Os",
		verbose = False,
		skip_programming = False,
		dry_run = False)
	sys.exit(rc)
#board_db = { "uno" : { "name":"uno board", "build.mcu" : "atmega328p", "build.f_cpu" : "16000000L", "upload.maximum_size" : "32000" } }

# ----------------------------------------------------------------------------

