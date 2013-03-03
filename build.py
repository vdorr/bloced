#!/usr/bin/env python

"""
standalone utility to compile avr-gcc programs
"""

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
import platform


try :
	from utils import here
except :
	def here(depth=None) :
		pass


try :
	from serial.tools.list_ports import comports
	from serial import Serial
	from serial.serialutil import SerialException
except :
	print("can not find appropriate version of pySerial")
	def comports() :
		return []


def __run_external(args, workdir=None, redir=False, tools_dir="") :
	redir_method = subprocess.PIPE if redir else None
	if tools_dir :
		arguments = (os.path.join(tools_dir, args[0]),) + tuple(args[1:])
	else :
		arguments = args
#	print here(), tools_dir
	try :
		p = subprocess.Popen(arguments,
			stdout=redir_method,
			stderr=subprocess.STDOUT,#redir_method
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


__SRC_EXTS = ( "*.c", "*.cpp" )
__HDR_EXTS = ( "*.h", "*.hpp" )

__re_src = __re_from_glob_list(__SRC_EXTS)
__re_hdr = __re_from_glob_list(__HDR_EXTS)


def list_resources(workdir, recurse,
		ignore=lambda fn: False,
		re_src=__re_src,
		re_hdr=__re_hdr,
		followlinks=True) :
	sources = []
	include_dirs = []
	tree = os.walk(workdir, followlinks=followlinks)
	src_total, idir_total = 0, 0
	for root, dirs, files in tree if recurse else islice(tree, 1) :
		src_files = [ os.path.join(workdir, root, fn) for fn in files if re_src.match(fn) ]
		src_total += len(src_files)
		sources += [ fn for fn in src_files if not ignore(fn) ]
		if any([ re_hdr.match(fn) for fn in files ]) :
			idir_total += 1
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


def get_board_types(all_in_one_arduino_dir=None) :
	_, _, boards_txt, _ = get_avr_arduino_paths(all_in_one_arduino_dir=all_in_one_arduino_dir)
	return __parse_boards(boards_txt)


def __print_streams(*v, **t) :
	t["term"].write("".join([ str(f) for f in v if f ]) + os.linesep)
#	print("".join([ f.decode("utf8", "replace") for f in v if f ]))


src_dir_t = namedtuple("src_dir", ["directory", "recurse"])


def build_source(board, source,
		aux_src_dirs=tuple(),
		aux_idirs=tuple(),
		boards_txt=None,
		libc_dir=None,
		defines=None,
		board_db=None,
		ignore_file="amkignore",
		ignore_lines=tuple(),
		prog_port=None,
		prog_driver="avrdude",
		prog_adapter="arduino",
		optimization="-Os",
		verbose=False,
		skip_programming=False,
		dry_run=False,
		blob_stream=None,
		term=sys.stdout) :
	"""
	blob_stream
		writable file-like object, of not None, hex file will be written to this file
	"""

	workdir = tempfile.mkdtemp()
	term.write("working directory '{0}'{1}".format(workdir, os.linesep))

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
		aux_idirs=aux_idirs,
		aux_src_dirs=aux_src_dirs,
		boards_txt=boards_txt,
		libc_dir=libc_dir,
		board_db=board_db,
		ignore_file=ignore_file,
		ignore_lines = ignore_lines,
		prog_port=prog_port,
		prog_driver=prog_driver,
		prog_adapter=prog_adapter,
		optimization=optimization,
		defines=defines,
		verbose=verbose,
		skip_programming=skip_programming,
		dry_run=dry_run,
		term=term),
#		a_out=a_out_f.name,
#		a_hex=a_hex_f.name)

	if blob_stream and r[0] :
		a_hex_f = open(os.path.join(workdir, "a.hex"), "r")
		shutil.copyfileobj(a_hex_f, blob_stream)
		a_hex_f.close()


	shutil.rmtree(workdir)

	return r


#def get_paths() :
#	return get_avr_arduino_paths(all_in_one_arduino_dir=None)


#def get_avr_arduino_enviroment(all_in_one_arduino_dir=None) :
#	libc_dir, tools_dir, target_files_dir  = get_avr_arduino_paths(
#		all_in_one_arduino_dir=all_in_one_arduino_dir)
#	return { "libc_dir" : libc_dir, "tools_dir" : tools_dir, "target_files_dir" : target_files_dir }


def get_avr_arduino_paths(all_in_one_arduino_dir=None) :
	"""
	return platform specific paths to arduino and avr lib/toolchain
	all_in_one_arduino_dir
		on windows, path to arduino installation directory
	"""
	system = platform.system()
	if system == "Windows" or (system == "Linux" and not all_in_one_arduino_dir is None) :
		libc_dir = os.path.join(all_in_one_arduino_dir, "hardware", "tools", "avr", "avr")
		tools_dir = os.path.join(all_in_one_arduino_dir, "hardware", "tools", "avr", "bin")
		target_files_dir = os.path.join(all_in_one_arduino_dir, "hardware", "arduino")
		boards_txt = os.path.join(target_files_dir, "boards.txt")
	elif system == "Linux" :
		libc_dir = "/usr/lib/avr"
		tools_dir = "/usr/bin"
		target_files_dir = "/usr/share/arduino/hardware/arduino/"
		boards_txt = "/usr/share/arduino/hardware/arduino/boards.txt"
	else :
		raise Exception("unsupported system: '" + system + "'")

	return libc_dir, tools_dir, boards_txt, target_files_dir


def build(board, workdir,
		wdir_recurse=True,
		aux_src_dirs=tuple(),
		aux_src_files=tuple(),
		aux_idirs=tuple(),
		boards_txt=None,
		libc_dir=None,
		tools_dir=None,
		board_db=None,
		ignore_file="amkignore",
		ignore_lines=tuple(),
		prog_port=None,
		prog_driver="avrdude",
		prog_adapter="arduino",
		optimization="-Os",
		defines=None,
		verbose=False,
		skip_programming=False,
		dry_run=False,
		a_out="a.out",
		a_hex="a.hex",
		term=sys.stdout
#		**args #rest of enviroment dict
		) :
	"""
	boards_txt
		path to arduino-style boards.txt
		at least this or board_db must be supplied
	skip_programming
		compile, create hex, but do not start programming driver
	dry_run
		as above, but use dry run of driver (avrdude -n)
	ignore_file
		path to file with ignored file, applied to all source dirs, including
		auxiliary one glob per line, lines starting with # are skipped
	aux_src_dirs
		list of tuples (str, bool) (directory, recurse)
	board_db
		appended to data from boards.txt, usefull if there is no boards.txt
		{ "uno" : {
			"name":"uno board",
			"build.mcu" : "atmega328p", #for avrdude/dfu-programmer
			"build.f_cpu" : "16000000L",
			"upload.maximum_size" : "32000" } }
	prog_adapter
		'arduino' for Arduino boards or None for dfu-programmer
	prog_driver
		supported options are 'avrdude' and 'dfu-programmer'
	defines
		dict of -Defines=\"for gcc\" in form { "efines" : "for gcc" }
	"""

	defines = {} if defines is None else defines
	board_info = {} if board_db is None else board_db

	if boards_txt :
		boards_txt_data = __parse_boards(boards_txt)
		if not boards_txt_data :
			print("failed to read boards info from '%s'" % boards_txt)
		else :
			board_info.update(boards_txt_data)
	if not board_info :
		term.write("got no board informations, quitting" + os.linesep)
		return (200,)

	src_dirs = (src_dir_t(workdir, True), ) + aux_src_dirs

	do_ignore = lambda fn: False
	ignores = []
	if workdir and ignore_file :
		ignores = __read_ignore(os.path.join(workdir, ignore_file))
		if ignores is None :
			ignores = []
			term.write("error reading ignore file" + os.linesep)

	ignores += list(ignore_lines)
#	pprint(ignores)
	ign_res = [ r for r in [ __ignore_to_re(ln) for ln in ignores ] if r ]
	re_ignore = re.compile("("+")|(".join(ign_res)+")")
	do_ignore = lambda fn: bool(ign_res) and bool(re_ignore.match(fn))

	sources, idirs = list(aux_src_files), list(aux_idirs)
	src_total, idir_total = 0, 0
	for directory, recurse in src_dirs:
		try :
			src, loc_idirs, srccnt, idircnt = list_resources(
				directory, recurse, ignore=do_ignore)
			src_total += srccnt
			idir_total += idircnt
		except StopIteration :
			term.write("can not access '{0}'{1}".format(ignore_file, os.linesep))
		else :
			sources += src
			idirs += loc_idirs
	if verbose :
		term.write("source files:")
		term.write(os.linesep)
#		pprint(source, sterm)

	mcu = board_info[board]["build.mcu"]
	f_cpu = board_info[board]["build.f_cpu"]
	flash_size = int(board_info[board]["upload.maximum_size"])
	prog_mcu = mcu.capitalize()

	term.write("{0} ({1} @ {2}MHz), {3}({4}) source files, {5}({6}) include directories{7}".format(
		board_info[board]["name"], mcu, int(f_cpu[:-1])/1000000,
		len(sources), src_total, len(idirs), idir_total, os.linesep))

	redir_streams = False

#	board_idirs = [ "/usr/lib/avr", "/usr/lib/avr/include",
#		"/usr/lib/avr/util", "/usr/lib/avr/compat" ]
#TODO remove avr specific directories
	board_idirs = ((tuple() if libc_dir is None else (libc_dir,)) + (
		os.path.join(libc_dir, "include"),
		os.path.join(libc_dir, "util"),
		os.path.join(libc_dir, "compat")))
	defs = { "F_CPU" : f_cpu }
	defs.update(defines)

	print(board_idirs+tuple(idirs))

	rc = gcc_compile(redir_streams, tuple(sources), os.path.join(workdir, a_out),
		mcu, optimization,
		tools_dir=tools_dir,
		defines=defs,
		i_dirs=board_idirs+tuple(idirs),
		l_libs = tuple(),#[ "/usr/lib/avr/lib/libc.a" ]
		term=term)
	if rc[0] :
		return rc

	run = partial(__run_external, workdir=workdir, redir=True, tools_dir=tools_dir)
#	run_loud = partial(__run_external, workdir=workdir, redir=False)
#	run_loud = run

	success, rc, streams = run(["avr-size", a_out])
	if success :
		stdoutdata, _ = streams
		head, val = stdoutdata.decode().split(os.linesep)[0:2]
		sizes = dict(zip(head.split(), val.split()))
		total_flash = int(sizes["text"])
		total_sram = int(sizes["data"])+int(sizes["bss"])
		term.write("memory usage: flash {0}B ({1:.1f}%), ram {2}B{3}".format
			(total_flash, total_flash*100.0/flash_size, total_sram, os.linesep))
		if total_flash > flash_size :
			term.write("input file is bigger than target flash!" + os.linesep)
	else :
		term.write("failed to execute avr-size" + os.linesep)
		return (20, )

	success, _, __ = run(["avr-objcopy",
		"--strip-debug",
		"-j", ".text",
		"-j", ".data", 
		"-O", "ihex", a_out, a_hex])
	if success :
		term.write("hex file created" + os.linesep)
	else :
		term.write("failed to execute avr-objcopy" + os.linesep)
		return (30, )

	rc = (0, )

	if not skip_programming :
		rc = program(prog_driver, prog_port, prog_adapter, prog_mcu, a_hex,
			verbose=verbose,
			dry_run=dry_run,
			term=term)

	return rc


def gcc_compile(redir_streams, sources, a_out, mcu, optimization,
		tools_dir="",
		defines=None,
		i_dirs=tuple(),
		l_libs=tuple(),
		l_dirs=tuple(),
		term=sys.stdout) :
	"""
	compile batch of c and/or c++ sources
	"""
	if not len(sources) :
		return (2001, "no_sources")
	include_dirs = tuple( "-I" + d for d in i_dirs )
	link_libs = tuple( "-l" + d for d in l_libs )
	link_dirs = tuple( "-L" + d for d in l_dirs )
	defs = tuple( "-D{0}={1}".format(k, v) for k, v in defines.items() ) if defines else tuple()
	common_args = include_dirs + l_libs + (optimization, "-mmcu=" + mcu) + defs

	extensions = __extract_extensions(sources)
	single_batch = all(e == extensions[0] for e in extensions)

	if single_batch :
		term.write("gcc compiling in single batch" + os.linesep)
		workdir = os.getcwd()
		run = partial(__run_external, workdir=workdir, redir=redir_streams, tools_dir=tools_dir)
		gcc_compile_sources(run, sources, common_args, out=a_out, term=term)
	else :
		objects = []
		args = ("-g", "-c", "-w") + common_args
		rc = None
		workdir = tempfile.mkdtemp()
		run = partial(__run_external, workdir=workdir, redir=redir_streams, tools_dir=tools_dir)
		term.write("gcc_compile working directory '{0}'{1}".format(workdir, os.linesep))
		try :
			for source, i in zip(sources, count()) :
				out = os.path.join(workdir, str(i) + os.path.extsep + "o")
				rc = gcc_compile_sources(run, (source,), args + ("-ffunction-sections",
					"-fdata-sections"), out=out)
				if rc[0] == 0 :
					term.write("compiled:{0} into {1}{2}".format(source, out, os.linesep))
					objects.append(os.path.split(out)[-1])
				else :
					break
		except Exception :
#			import traceback
#			print here(), traceback.format_exc()
			rc = (666, )

		if rc is None or not rc[0] :
			success, gcc_rc, streams = run(("avr-gcc", "-Wl,--gc-sections", #from build_arduino.py
				optimization, "-o", a_out, "-lm", "-t") + (optimization, "-mmcu=" + mcu) +
				tuple(objects) + link_libs + link_dirs)
#			print here(), gcc_rc, success, objects, workdir, a_out, streams

		shutil.rmtree(workdir)

		if not rc is None :
			return rc

		if success :
			stdoutdata, stderrdata = streams
			__print_streams("linked", " ", stdoutdata, stderrdata, term=term)
		else :
			stdoutdata, stderrdata = streams
			__print_streams("failed to link with avr-gcc", " ",
				stdoutdata, stderrdata, term=term)
			return (10, )
	return (0, )


def __extract_extensions(l, lower=True) :
	return [ (e.lower() if lower else e) for e in
		(s.split(os.path.extsep)[-1] for s in l) ]


def gcc_compile_sources(run, sources, common_args, out=None, term=sys.stdout) :
	"""
	compile one or multiple source files of the same type (c or c++) with gcc/g++
	"""
	if not len(sources) :
		return (1001, "no_sources")

	extensions = __extract_extensions(sources)
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
	success, _, streams = run((compiler, "-g", "-w",
		"-ffunction-sections", "-fdata-sections") + common_args + sources +
		(('-o', out) if out else tuple()))

	if success :
		stdoutdata, stderrdata = streams
		__print_streams("compiled", " ", stdoutdata, stderrdata, term=term)
		return (0, )
	else :
		stdoutdata, stderrdata = streams
		__print_streams("failed to execute avr-gcc", " ",
			stdoutdata, stderrdata, term=term)
		return (10, "gcc_failed")


def program(prog_driver, prog_port, prog_adapter, prog_mcu, a_hex,
		a_hex_blob=None,
		verbose=False,
		dry_run=False,
		term=sys.stdout) :
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

	if filename is None :
		return (50, )

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


def main() :

	import argparse
	parser = argparse.ArgumentParser(description="build")
	parser.add_argument("action", metavar="action", type=str, nargs=1,
		default="b",
		help="Action to perform" + os.linesep
			+ "\tb - build" + os.linesep
			+ "\tp - program" + os.linesep
			+ "\tbp - build and program")
	parser.add_argument("--brd", metavar="board", type=str, nargs=1,
		default="uno", help="Target Arduino Board")
	parser.add_argument("--port", metavar="port", type=str, nargs=1,
		default="/dev/ttyACM0", help="Programmer Port")
	parser.add_argument("--ignore", metavar="ignore", type=str, nargs=1,
		default="amkignore", help="IgnoreFile Path")
#	parser.add_argument("--out", metavar="out", type=str, nargs=1,
#		default="a.out", help="Output File")
	args = parser.parse_args()
#	print here(), args
#	sys.exit(0)

	libc_dir, tools_dir, boards_txt, target_files_dir = get_avr_arduino_paths(all_in_one_arduino_dir=None)

	board_info = get_board_types()[args.brd]
	variant = board_info["build.variant"] if "build.variant" in board_info else "standard" 

	work_dir = os.getcwd()
	source_dirs = tuple()#in dfs derived from libs

	do_programming = "p" in args.action[0]

#	print here(), args.action, "p" in args.action

#	with open(args.out, "w") as blob_stream :
	if 1 :
		rc = build(args.brd, work_dir,
			wdir_recurse = True,
			aux_src_dirs=(
				("/usr/share/arduino/libraries/Wire", True),#recurse
				(os.path.join(target_files_dir, "cores", "arduino"), False),
				(os.path.join(target_files_dir, "variants", variant), False),
#				(os.path.join(install_path, "library", "arduino"), False),
			) + tuple( (path, True) for path in source_dirs ),
			aux_idirs=[ "/usr/share/arduino/libraries/Wire" ],#os.path.join(install_path, "target", "arduino", "include") ],
			boards_txt=boards_txt,
			libc_dir=libc_dir,
#			board_db={},
			ignore_file=args.ignore,
#			ignore_lines=( "*.cpp", "*.hpp", "*" + os.path.sep + "main.cpp", ), #TODO remove this filter with adding cpp support to build.py
			ignore_lines=( "*" + os.path.sep + "main.cpp", ),
			prog_port=args.port,
			prog_driver="avrdude", # or "dfu-programmer"
			prog_adapter="arduino", #None for dfu-programmer
			optimization="-Os",
			verbose=True,
			skip_programming=not do_programming,#False,
#			dry_run=False,
#			blob_stream=blob_stream,
			term=sys.stdout)

#	rc, = build("uno", os.getcwd(),
#		wdir_recurse = True,
#		libc_dir = libc_dir,
#		tools_dir = tools_dir,
#		aux_src_dirs = [ src_dir_t(os.path.join(target_files_dir, "cores", "arduino"), False) ],
#		boards_txt = boards_txt,
#		ignore_file = "amkignore",
#		prog_port = "/dev/ttyACM0",
#		prog_driver = "avrdude", # or "dfu-programmer"
#		prog_adapter = "arduino", #None for dfu-programmer
#		optimization = "-Os",
#		verbose = False,
#		skip_programming = False,
#		dry_run = False)

	sys.exit(rc)

#	board_db = {
#		"uno" : {
#			"name" : "uno board",
#			"build.mcu" : "atmega328p",
#			"build.f_cpu" : "16000000L",
#			"upload.maximum_size" : "32000"
#			}
#		}


if __name__ == "__main__" :
	main()


# ----------------------------------------------------------------------------

