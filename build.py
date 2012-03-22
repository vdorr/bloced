

#TODO use as gedit plugin

import sys
import subprocess
import os
import tempfile
from functools import partial
import fnmatch
import re
from pprint import pprint
from collections import namedtuple, OrderedDict
from itertools import islice, count
import shutil

try :
	from serial.tools.list_ports import comports
	from serial import Serial
	from serial.serialutil import SerialException
except :
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
	except Exception as e:
		print(e) #XXX
		return (False, None, (None, None))
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
	board_info = OrderedDict()
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
		aux_src_dirs=[],
		boards_txt=None,
		board_db={},
		ignore_file="amkignore",
		ignore_lines=[],
		prog_port=None,
		prog_driver="avrdude", # or "dfu-programmer"
		prog_adapter="arduino", #None for dfu-programmer
		optimization="-Os",
		verbose=False,
		skip_programming=False,
		dry_run=False,
		blob_stream=None) :
	"""
blob_stream
	writable file-like object, of not None, hex file will be written to this file
	"""

	workdir = tempfile.mkdtemp()
	print("working directory '%s'" % workdir)

	source_f = open(os.path.join(workdir, "source.c"), "w")
#	a_out_f = open(os.path.join(workdir, "a.out"), "w")
#	a_hex_f = open(os.path.join(workdir, "a.hex"), "w")
#	a_out_f.close()
#	a_hex_f.close()

	source_f.write(source)
	source_f.write(os.linesep)
	source_f.close()

	r = build(board, workdir,
		wdir_recurse=False,
#		aux_src_files=[ source_f.name ],#XXX
		aux_src_dirs=aux_src_dirs,
		boards_txt=boards_txt,
		board_db=board_db,
		ignore_file=ignore_file,
		ignore_lines = ignore_lines,
		prog_port=prog_port,
		prog_driver=prog_driver,
		prog_adapter=prog_adapter,
		optimization=optimization,
		verbose=verbose,
		skip_programming=skip_programming,
		dry_run=dry_run),
#		a_out=a_out_f.name,
#		a_hex=a_hex_f.name)

	if blob_stream and r[0] :
		a_hex_f = open(os.path.join(workdir, "a.hex"), "r")
		shutil.copyfileobj(a_hex_f, blob_stream)
		a_hex_f.close()


	shutil.rmtree(workdir)

	return r


#TODO
def compile_incforth() :
	pass


def compile_gcc() :
	pass


def build(board, workdir,
		wdir_recurse=True,
		aux_src_dirs=[],
		aux_src_files=[],
		boards_txt=None,
		board_db={},
		ignore_file="amkignore",
		ignore_lines=[], #TODO TODO TODO
		prog_port=None,
		prog_driver="avrdude", # or "dfu-programmer"
		prog_adapter="arduino", #None for dfu-programmer
		optimization="-Os",
		verbose=False,
		skip_programming=False,
		dry_run=False,
		a_out="a.out",
		a_hex="a.hex" ) :
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
	list of tuples (str, bool) (directory, recurse)
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
	ignores = []
	if workdir and ignore_file :
		ignores = __read_ignore(os.path.join(workdir, ignore_file))
		if ignores is None :
			ignores = []
			print("error reading ignore file '%s'" % ignore_file)
	ignores += ignore_lines
#	pprint(ignores)
	ign_res = [ r for r in [ __ignore_to_re(ln) for ln in ignores ] if r ]
	re_ignore = re.compile("("+")|(".join(ign_res)+")")
	do_ignore = lambda fn: bool(ign_res) and bool(re_ignore.match(fn))

	sources, idirs = list(aux_src_files), []
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
	if verbose :
		print("source files:")
		pprint(sources)

	mcu = board_info[board]["build.mcu"]
	f_cpu = board_info[board]["build.f_cpu"]
	flash_size = int(board_info[board]["upload.maximum_size"])
	prog_mcu = mcu.capitalize()

	print("%s (%s @ %iMHz), %i(%i) source files, %i(%i) include directories" %
		(board_info[board]["name"], mcu, int(f_cpu[:-1])/1000000,
		len(sources), src_total, len(idirs), idir_total))

	run = partial(__run_external, workdir=workdir, redir=True)
#	run_loud = partial(__run_external, workdir=workdir, redir=False)
	run_loud = run

	board_idirs = [ "/usr/lib/avr", "/usr/lib/avr/include",
		"/usr/lib/avr/util", "/usr/lib/avr/compat" ]
	defs = { "F_CPU" : f_cpu }
	rc = gcc_compile(run_loud, sources, a_out, mcu, optimization,
		defines=defs,
		i_dirs=board_idirs+idirs,
		l_libs = [])#[ "/usr/lib/avr/lib/libc.a" ]
	if rc[0] :
		return rc

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

	rc = (0, )

	if not skip_programming :
		rc = program(prog_driver, prog_port, prog_adapter, prog_mcu, a_hex,
			verbose=verbose,
			dry_run=dry_run)

	return rc


def gcc_compile(run, sources, a_out, mcu, optimization,
		defines={},
		i_dirs=[],
		l_libs = [],
		l_dirs=[]
	) :

	include_dirs = [ "-I" + d for d in i_dirs ]
	link_libs = [ "-l" + d for d in l_libs ]
	link_dirs = [ "-L" + d for d in l_dirs ]
	defs = [ "-D{0}={1}".format(k, v) for k, v in defines.items() ]
	common_args = include_dirs + l_libs + [ optimization, "-mmcu=" + mcu ] + defs

#XXX
	single_batch = False

	if single_batch :
		gcc_compile_sources(run, sources, common_args, out=a_out)
	else :

		workdir = tempfile.mkdtemp()
		print("gcc_compile working directory '{0}'".format(workdir))


		objects = []

		args = ["-g", "-c", "-w"] + common_args

		rc = None

		for source, i in zip(sources, count()) :

			if 0 :
#				out = source + os.path.extsep + "o"
				out=os.path.join(workdir, source + os.path.extsep + "o")
			else :
				ext = source.split(os.path.extsep)[-1].lower()
				out = str(i) + os.path.extsep + "o"
	#			out = source[:-len(ext)] + "o"

			rc = gcc_compile_sources(run, [source], args + ["-ffunction-sections",
				"-fdata-sections", "-o", out])

#			print rc

			if rc[0] == 0 :
				print "compiled:", out
				objects.append(os.path.split(out)[-1])
			else :
				break

		if rc is None :
#			print("linking!!!!", objects)
			#from build_arduino.py
			success, _, streams = run(["avr-gcc", "-Wl,--gc-sections",
				optimization, "-o", a_out, "-lm",] +
				objects + link_libs + link_dirs)

		shutil.rmtree(workdir)

		if not rc is None :
			return rc

		if success :
			stdoutdata, stderrdata = streams
			__print_streams("linked", " ", stdoutdata, stderrdata)
		else :
			stdoutdata, stderrdata = streams
			__print_streams("failed to link with avr-gcc", " ",
				stdoutdata, stderrdata)
			return (10, )


	return (0, )


def gcc_compile_sources(run, sources, common_args, out=None) :
	"""
	compile one or multiple source files of same type (c or c++) with gcc
	"""
	if not len(sources) :
		return (1001, "no_sources")

	extensions = [ s.split(os.path.extsep)[-1].lower() for s in sources ]
	ext = extensions[0]

	if len(extensions) > 1 and not all( e == ext for e in extensions) :
		return (1002, "sources_not_of_single_type")

	if ext == "c" :
		compiler = "avr-gcc"
	elif ext in ( "cpp", "c++", "cxx" ) :
		compiler = "avr-g++"
	else :
		return (1003, "unknown_source_type")
#from build_arduino.py
#  cmdline = '%(avr_path)s%(compiler)s -c %(verbose)s -g -Os -w -ffunction-sections -fdata-sections
#-mmcu=%(arch)s -DF_CPU=%(clock)dL -DARDUINO=%(env_version)d %(include_dirs)s %(source)s -o%(target)s' %
	success, _, streams = run([compiler, "-g", "-w",
		"-ffunction-sections", "-fdata-sections"] +
		(['-o', out] if out else []) + common_args + sources)

	if success :
		stdoutdata, stderrdata = streams
		__print_streams("compiled", " ", stdoutdata, stderrdata)
		return (0, )
	else :
		stdoutdata, stderrdata = streams
		__print_streams("failed to execute avr-gcc", " ",
			stdoutdata, stderrdata)
		return (10, "gcc_failed")


def program(prog_driver, prog_port, prog_adapter, prog_mcu, a_hex,
		a_hex_blob=None,
		verbose=False,
		dry_run=False) :
	drivers = {
		"avrdude" : program_avrdude,
		"dfu-programmer" : program_dfu_programmer,
	}
	if prog_driver in drivers :
		driver = drivers[prog_driver]
	else :
		print("unknown programmer driver '{0}'".format(prog_driver))
		return (40, )

	if a_hex is None and a_hex_blob :
		f = tempfile.NamedTemporaryFile(suffix=".hex")#is suffix needed?
		f.write(a_hex_blob)
		f.flush()
		filename = f.name
	else :
		filename = a_hex

	print("filename=", filename)

	rc = driver(prog_driver, prog_port, prog_adapter, prog_mcu, filename,
		verbose=verbose,
		dry_run=dry_run)

	if a_hex is None and a_hex_blob :
		f.close()

	return rc


#TODO stdin input mode
def program_avrdude(prog_driver, prog_port, prog_adapter, prog_mcu, a_hex,
		a_hex_blob=None,
		verbose=False,
		dry_run=False,
		workdir=os.getcwd()) :

#	run = partial(__run_external, workdir=workdir, redir=True)
	run = partial(__run_external, workdir=workdir, redir=False)

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
		stderrstr = "None" if stderrdata is None else stderrdata.decode() 
		print("failed to run avrdude '{0}'".format(stderrstr))
		return (40, )
	return (0, )


def program_dfu_programmer(prog_driver, prog_port, prog_adapter, prog_mcu, a_hex,
		a_hex_blob=None,
		verbose=False,
		dry_run=False,
		workdir=os.getcwd()) :

	run = partial(__run_external, workdir=workdir, redir=True)
#	run_loud = partial(__run_external, workdir=workdir, redir=False)

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

