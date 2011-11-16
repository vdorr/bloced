
####import sys
from sys import exit
import subprocess
import os
import tempfile
from functools import partial
import fnmatch
import re
import string
from pprint import pprint

# ----------------------------------------------------------------------------

#TODO use as gedit plugin
#TODO ".buildignore"

def __run_external(args, workdir=None) :
	try :
		p = subprocess.Popen(args,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			cwd=os.getcwd() if workdir is None else workdir )
	except :
		return (False, None, tuple())
	else :
		(stdoutdata, stderrdata) = p.communicate()
		if p.returncode == 0 :
			return (True, p.returncode, (stdoutdata, stderrdata))
		else :
			return (False, p.returncode, (stdoutdata, stderrdata))


def __list_files(workdir, recurse) :
	file_list = []
	tree = os.walk(workdir)
	for root, dirs, files in tree if recurse else [ tree.next() ] :
		file_list += [ os.path.join(workdir, root, fn) for fn in files]
	return file_list


def __read_ignore(fname) :
	try :
		f = open(fname, "r")
		lines = f.readlines()
		f.close()
		return [ ln.strip() for ln in lines if ln.strip() ]
	except :
		return None
#fnmatch.filter(names, pattern)


def __parse_boards_line(line) :
	key, value = line.split("=")
	return line


def __parse_boards(board_txt) :
	try :
		f = open(board_txt, "r")
		lines = f.readlines()
		f.close()
	except :
		return None

	valid = re.compile("\s*\w+\.\S+\s*=\s*\S+")

#	items = [ __parse_boards_line(ln) for ln in lines if valid.match(ln) ]

	board_info = {}
	for line in [ ln for ln in lines if valid.match(ln) ] :
		key, value = line.split("=")
		dot = key.index(".")
		board_name = key[0:dot]
		if not board_name in board_info :
			board_info[board_name] = {}
		board_info[board_name][key[dot+1:]] = value.strip()

	return board_info


__source_file_exts = [
	"*.c",
	"*.h",
	"*.cpp",
	"*.hpp",
]

def build() :
	workdir = os.getcwd()

	ignores = __read_ignore(os.path.join(workdir, ".amkignore"))
	ign_res = [ fnmatch.translate(ln) for ln in ignores ]
#	print "("+string.join(ign_res, ")|(")+")"
	re_ignore = re.compile("("+string.join(ign_res, ")|(")+")")

	src_res = [ fnmatch.translate(ln) for ln in __source_file_exts ]
	re_source = re.compile("("+string.join(src_res, ")|(")+")")
#	print "("+string.join(src_res, ")|(")+")"

	files = __list_files(workdir, True)
#	print files
	sources = [ fn for fn in files
		if re_source.match(fn) and not re_ignore.match(fn) ]
	print sources

	board_txt = "/usr/share/arduino/hardware/arduino/boards.txt"
	board_info = __parse_boards(board_txt)
	pprint(board_info)

	exit(0)

	run = partial(__run_external, workdir=workdir)

#	a_out_f = tempfile.NamedTemporaryFile()
#	a_hex_f = tempfile.NamedTemporaryFile()
#	a_out = a_out_f.name
#	a_hex = a_hex_f.name

	a_out, a_hex = "a.out", "a.hex"
	i_dirs = []#[ "/usr/lib/avr", "/usr/lib/avr/include", "/usr/lib/avr/util", "/usr/lib/avr/compat" ]
#"/usr/share/arduino/hardware/arduino/cores/arduino"
	l_libs = []#[ "/usr/lib/avr/lib/libc.a" ]

	optimization = "-Os"
	mcu = "atmega328"
	f_cpu = 16000000
	
	prog_mcu = "m328p"
	prog_port = "/dev/ttyACM0"

	gcc_args = i_dirs + l_libs + [ optimization, "-mmcu=" + mcu, "-DF_CPU=%i" % f_cpu, "-o", a_out ]
	gcc_args += ["tst.c"]

	success, _, __ = run(["avr-gcc"] + gcc_args)
	if success :
		print("compiled")
	else :
		print("failed to execute avr-gcc")
		sys.exit(10)
#	try :
#		p = subprocess.Popen(["avr-gcc"] + gcc_args,
#			stdout=subprocess.PIPE,
#			stderr=subprocess.PIPE,
#			cwd=workdir)
#	except :
#		print("failed to execute avr-gcc")
#	else :
#		(stdoutdata, stderrdata) = p.communicate()
#		if p.returncode == 0 :
#			print("compiled")
#		else :
#			print("failed to execute avr-gcc")

	success, rc, streams = run(["avr-size", a_out])
	if success :
		stdoutdata, _ = streams
		head, val = stdoutdata.split(os.linesep)[0:2]
		sizes = dict(zip(head.split(), val.split()))
		print("memory usage: flash %iB, ram %iB" %
			(int(sizes["text"]),
			int(sizes["data"])+int(sizes["bss"])))
	else :
		print("failed to execute avr-size")
		sys.exit(20)


#	try :
#		p = subprocess.Popen(["avr-size", a_out],
#			stdout=subprocess.PIPE,
#			stderr=subprocess.PIPE,
#			cwd=workdir)
#	except :
#		print("failed to execute avr-size")
#	else :
#		(stdoutdata, stderrdata) = p.communicate()
#		if p.returncode == 0 :
#			head, val = stdoutdata.split(os.linesep)[0:2]
#			sizes = dict(zip(head.split(), val.split()))
#			print("memory usage: flash %iB, ram %iB" %
#				(int(sizes["text"]), int(sizes["data"])+int(sizes["bss"])))
#		else :
#			print("failed to execute avr-size")

	success, _, __ = run(["avr-objcopy", "-j", ".text", "-j", ".data" "-O" "ihex", a_out, a_hex])
	if success :
		print("hex file created")
	else :
		print("failed to execute avr-objcopy")
		sys.exit(30)

#	try :
#		p = subprocess.Popen(
#			["avr-objcopy", "-j", ".text", "-j", ".data" "-O" "ihex", a_out, a_hex],
#			cwd=workdir)
#	except :
#		print("failed to execute avr-objcopy")
#	else :
#		p.communicate()
#		if p.returncode == 0 :
#			pass
#		else :
#			print("failed to execute avr-objcopy")

	success, _, streams = run(["avrdude", "-q", "-n", "-c"+"arduino", "-P" + prog_port, "-p" + prog_mcu, "-Uflash:w:" + a_hex + ":i"])
#	success, _, streams = run(["avrdude", "-q", "-n", "-c"+"arduino", "-Pusb", "-p" + prog_mcu, "-U flash:w:" + a_hex + ":i"])
	if success :
		print("succesfully uploaded")
	else :
		stdoutdata, stderrdata = streams
		print("failed to run avrdude '%s'" % stderrdata)
		sys.exit(40)

#	try :
#		p = subprocess.Popen(
#			["avrdude", "-q", "-n", "-c"+"arduino", "-P " + prog_port, "-p" + prog_mcu, "-U flash:w:" + a_hex + ":i"],
#			cwd=workdir)
#	except :
#		print("failed to run avrdude")
#	else :
#		p.communicate()
#		if p.returncode == 0 :
#			pass
#		else :
#			print("failed to run avrdude")

#XXX
#	exit(666)

# ----------------------------------------------------------------------------

if __name__ == "__main__" :
	build()

# ----------------------------------------------------------------------------

