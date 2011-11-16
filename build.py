
####import sys
import sys
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


#def __list_files(workdir, recurse) :
#	file_list = []
#	tree = os.walk(workdir)
#	for root, dirs, files in tree if recurse else [ tree.next() ] :
#		file_list += [ os.path.join(workdir, root, fn) for fn in files ]
#	return file_list


__src_exts = ( "*.c", "*.cpp" )
__hdr_exts = ( "*.h", "*.hpp" )

__re_src = re.compile("("+string.join([ fnmatch.translate(ln) for ln in __src_exts ], ")|(")+")")
__re_hdr = re.compile("("+string.join([ fnmatch.translate(ln) for ln in __hdr_exts ], ")|(")+")")


def __list_files(workdir, recurse) :
	sources = []
	inlude_dirs = []
	tree = os.walk(workdir)
	for root, dirs, files in tree if recurse else [ tree.next() ] :
		sources += [ os.path.join(workdir, root, fn)
			for fn in files if __re_src.match(fn) ]
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


def build() :
	boards_txt = "/usr/share/arduino/hardware/arduino/boards.txt"
	arduino_src_dir = "/usr/share/arduino/hardware/arduino/cores/arduino"
	board = "uno"
	ignore_file = ".amkignore"
	prog_port = "/dev/ttyACM0"
	workdir = os.getcwd()
	wdir_recurse = True

	ignores = __read_ignore(os.path.join(workdir, ignore_file))
	ign_res = [ fnmatch.translate(ln) for ln in ignores ]
#	print "("+string.join(ign_res, ")|(")+")"
	re_ignore = re.compile("("+string.join(ign_res, ")|(")+")")

#	src_res = [ fnmatch.translate(ln) for ln in __src_exts ]
#	re_source = re.compile("("+string.join(src_res, ")|(")+")")
#	print "("+string.join(src_res, ")|(")+")"

#	files = __list_files(workdir, True)
#	print files
#	sources = [ fn for fn in files
#		if re_source.match(fn) and not re_ignore.match(fn) ]

	ard_sources, ard_idirs = [], []#__list_files(arduino_src_dir, False)#TODO

	sources, loc_idirs = __list_files(workdir, wdir_recurse)

	board_info = __parse_boards(boards_txt)
#	pprint(board_info)


	print board_info[board]["name"]

	mcu = board_info[board]["build.mcu"]
	f_cpu = board_info[board]["build.f_cpu"]
	flash_size = int(board_info[board]["upload.maximum_size"])
	prog_mcu = mcu.capitalize() #"m328p"

	run = partial(__run_external, workdir=workdir)

#	a_out_f = tempfile.NamedTemporaryFile()
#	a_hex_f = tempfile.NamedTemporaryFile()
#	a_out = a_out_f.name
#	a_hex = a_hex_f.name

	board_idirs = [ "/usr/lib/avr", "/usr/lib/avr/include",
		"/usr/lib/avr/util", "/usr/lib/avr/compat" ]
	a_out, a_hex = "a.out", "a.hex"
	i_dirs = [ "-I" + d for d in ( loc_idirs + board_idirs + ard_idirs ) ]
#""
	l_libs = []#[ "/usr/lib/avr/lib/libc.a" ]

	optimization = "-Os"

	gcc_args = i_dirs + l_libs + [ optimization, "-mmcu=" + mcu,
		"-DF_CPU=%s" % f_cpu, "-o", a_out ]
	gcc_args += sources + ard_sources#["tst.c"]

	success, _, streams = run(["avr-gcc"] + gcc_args)
	if success :
		stdoutdata, stderrdata = streams
		print("compiled" + " " + stdoutdata + stderrdata)
	else :
		stdoutdata, stderrdata = streams
		print("failed to execute avr-gcc" + " " + stdoutdata + stderrdata)
		sys.exit(10)

	success, rc, streams = run(["avr-size", a_out])
	if success :
		stdoutdata, _ = streams
		head, val = stdoutdata.split(os.linesep)[0:2]
		sizes = dict(zip(head.split(), val.split()))
#TODO check against boards.txt
		print("memory usage: flash %iB, ram %iB" %
			(int(sizes["text"]),
			int(sizes["data"])+int(sizes["bss"])))
	else :
		print("failed to execute avr-size")
		sys.exit(20)

	success, _, __ = run(["avr-objcopy", "-j", ".text", "-j",
		".data" "-O" "ihex", a_out, a_hex])
	if success :
		print("hex file created")
	else :
		print("failed to execute avr-objcopy")
		sys.exit(30)




	sys.exit(0)





	success, _, streams = run(["avrdude", "-q", "-n", "-c"+"arduino",
		"-P" + prog_port,
		"-p" + prog_mcu,
		"-Uflash:w:" + a_hex + ":i"])
	if success :
		print("succesfully uploaded")
	else :
		stdoutdata, stderrdata = streams
		print("failed to run avrdude '%s'" % stderrdata)
		sys.exit(40)

# ----------------------------------------------------------------------------

if __name__ == "__main__" :
	build()

# ----------------------------------------------------------------------------

