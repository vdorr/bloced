#!/usr/bin/python

import sys
import os
import traceback
import time

if sys.version_info.major == 3 :
	import io
else :
	import StringIO as io

import dfs
import serializer
import implement
import core
import ccodegen
import build

from utils import here


USAGE = """
Usage:
chain.py action file.w
action - g|b|p
	g - generate
	b - build
	p - program
"""


USE_CACHE = True


def cache_get_probes(cache, w) :
	rev_my = w.get_revision()
	if rev_my is None :
		return False, None
	with open(cache.path("probes_cache"), "rb") as f :
		try :
			rev_cached, timestamp, probes_list = serializer.load(f)
		except Exception as e :
			print(here(), e)
			return False, None
	if rev_my == rev_cached :
		return True, (timestamp, probes_list)
	else :
		return False, None


def cache_get_blob(cache) :
	revision = w.get_revision()


def build_workbench(w_data, term_stream, cache, blockfactory, msgq, all_in_one_arduino_dir) :
#TODO workbench_generate_code need to be split to take advanrage od caching generated code
	w, board_type, variant, source, source_dirs, probes = workbench_generate_code(w_data,
		blockfactory, msgq)
	revision = w.get_revision()
#TODO we need to look revision of libraries
#TODO cache probes
	print(source)
#TODO cache source

	build_workdir = None

	if USE_CACHE and not cache is None and not revision is None:
		build_workdir = cache.path("build")
		if probes :
			probes_cache = cache.path("probes_cache")
			with open(probes_cache, "wb") as f :
				serializer.dump((revision, time.time(), probes), f)

	build_rc, blob_stream = compile_worbench(w, board_type, variant, source, source_dirs,
		all_in_one_arduino_dir, build_workdir, msgq, term_stream)
#	print(here(), w.get_revision())
#TODO cache blob and object files
	return build_rc, blob_stream, probes


def workbench_generate_code(w_data, blockfactory, msgq) :
	try :
#TODO reduce number of statements within try block
		w = dfs.Workbench(passive=True, do_create_block_factory=False,
			blockfactory=blockfactory)
		w.loading = True #to keep revision number

		local_lib = core.BasicBlocksFactory(load_basic_blocks=False)
		local_lib.load_standalone_workbench_lib(None, "<local>",
			library=w.blockfactory,
			w_data=w_data)
		library = core.SuperLibrary([w.blockfactory, local_lib])
		serializer.restore_workbench(w_data, w,
			use_cached_proto=False,
			library=library)
	except Exception as e:
		print(here(), traceback.format_exc())
		msgq.int_msg_put("status", args=("build", False, str(e)))
		return None

	board_type = w.get_board()

	if board_type is None :
		msgq.int_msg_put("status", args=("build", False, "board_type_not_set"))
		return None

	board_info = build.get_board_types()[board_type]
	variant = board_info["build.variant"] if "build.variant" in board_info else "standard" 

	msgq.int_msg_put("status", args=("build", True, "build_started"))

	out_fobj = io.StringIO()
	try :
		libs_used, probes = implement.implement_workbench(w, w.sheets, w.get_meta(),
			ccodegen, core.KNOWN_TYPES, library, out_fobj)
	except Exception as e:
		print(here(), traceback.format_exc())
		msgq.int_msg_put("status", args=("build", False, str(e)))
		return None

	if out_fobj.tell() < 1 :
		msgq.int_msg_put("status", args=("build", False, "no_code_generated"))
		return None

	source = out_fobj.getvalue()

	source_dirs = set()
	for l in library.libs :
		if l.name in libs_used :
			for src_file in l.source_files :
				source_dirs.add(os.path.dirname(src_file))

	return w, board_type, variant, source, source_dirs, probes


def compile_worbench(w, board_type, variant, source, source_dirs, all_in_one_arduino_dir,
		build_workdir, msgq, term_stream) :

	libc_dir, tools_dir, boards_txt, target_files_dir, all_in_one_arduino_dir = build.get_avr_arduino_paths(
		all_in_one_arduino_dir=all_in_one_arduino_dir)

	install_path = os.getcwd()#XXX replace os.getcwd() with path to dir with executable file

	defines = {}
	defines["ARDUINO"] = 100 #FIXME determine "correct" value
	if w.get_gateway_enabled() :
		defines["DBG_ENABLE_GATEWAY"] = 1

	blob_stream = io.StringIO()

#	try :
	if 1 :
		build_rc, o_files = build.build_source(board_type, source,
			workdir_in=build_workdir,
			aux_src_dirs=(
				(os.path.join(target_files_dir, "cores", "arduino"), False),
				(os.path.join(target_files_dir, "variants", variant), False),
#					(os.path.join(install_path, "library", "arduino"), False),
				(os.path.join(all_in_one_arduino_dir, "libraries"), True),
			) + tuple( (path, True) for path in source_dirs ),#TODO derive from libraries used
			aux_idirs=[ os.path.join(install_path, "target", "arduino", "include") ],
			boards_txt=boards_txt,
			libc_dir=libc_dir,
#			board_db={},
			ignore_file=None,#"amkignore",
#			ignore_lines=( "*.cpp", "*.hpp", "*" + os.path.sep + "main.cpp", ), #TODO remove this filter with adding cpp support to build.py
			ignore_lines=( "*" + os.path.sep + "main.cpp", "*Esplora*", "*WiFi*"),
#			prog_port=None,
#			prog_driver="avrdude", # or "dfu-programmer"
#			prog_adapter="arduino", #None for dfu-programmer
			optimization="-Os",
			defines=defines,
			verbose=False,
			skip_programming=True,#False,
#			dry_run=False,
			blob_stream=blob_stream,
			term=term_stream)
#	except Exception as e :
##		print here(), str(e)
#		raise e
#		msgq.int_msg_put("status", args=("build", False, "compilation_failed"),
#			kwargs={"term_stream" : str(e)})
#		return None

	print(here(), build_rc, o_files, blob_stream.tell())

	return build_rc, blob_stream.getvalue()


def write_program(prog_mcu, port, blob) :
	rc = build.program("avrdude", port, "arduino", prog_mcu, None,
		a_hex_blob=blob,
		verbose=False,
		dry_run=False)
	return rc


def execute(action, fname) :
	cache = serializer.Cache(new_filename, True)

	if "g" in actions :
		print(here())

	if "b" in actions :
		print(here())

	if "p" in actions :
		print(here())


def main(argv) :
	try :
		_, actions, fname = sys.argv
	except :
		print("expected exactly 2 arguments")
		sys.stdout.write(USAGE)
		exit(100)
	if not all(c in "gbp" for c in actions) :
		print("invalid action")
		sys.stdout.write(USAGE)
		exit(101)
	if not os.path.isfile(fname) :
		print("file not found")
		sys.stdout.write(USAGE)
		exit(102)
	execute(action, fname)


if __name__ == "__main__" :
	main(sys.argv)


