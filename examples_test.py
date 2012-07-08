#!/usr/bin/env python


"""
list, load and build all workbench file in ./examples directory
"""


from sys import version_info
if version_info.major == 3 :
	from io import StringIO
else :
	from StringIO import StringIO

import os
import sys
import traceback
import time
from pprint import pprint

import dfs
import core
import serializer
import implement
import ccodegen
import build

from utils import here


def get_files(d):
	file_list = []
	for root, _, files in os.walk(d) :
		for fn in files :
			if os.path.splitext(fn)[-1] == ".w" :
				file_list.append(os.path.abspath(os.path.join(root, fn)))
	return file_list


def main() :
	started = time.time()

	files = get_files("./examples")
#	print here(), files

	main_lib = core.create_block_factory(scan_dir=os.path.join(os.getcwd(), "library"))

#	all_in_one_arduino_dir = self.config.get("Path", "all_in_one_arduino_dir")
	libc_dir, tools_dir, boards_txt, target_files_dir = build.get_avr_arduino_paths()

	failed = []
	succeeded = []

	for fname in files :

		print here(), "loading:", fname

		local_lib = core.BasicBlocksFactory(load_basic_blocks=False)

		try :
			local_lib.load_standalone_workbench_lib(fname, "<local>")
		except Exception :
			print(here())
			traceback.print_exc()
			failed.append((fname, "loading_as_library"))
			continue

		library = core.SuperLibrary([main_lib, local_lib])

		w = dfs.Workbench(passive=True)

		try :
			with open(fname, "rb") as f :
				serializer.unpickle_workbench(f, w, use_cached_proto=False, library=library)
		except Exception :
			print(here())
			traceback.print_exc()
			failed.append((fname, "loading_worbench"))
			continue

		sheets = w.sheets
		global_meta = w.get_meta()

		out_fobj = StringIO()

		try :
			libs_used, = implement.implement_workbench(w, sheets, global_meta,
				ccodegen, core.KNOWN_TYPES, library, out_fobj)#sys.stdout)
		except Exception :
			print(here())
			traceback.print_exc()
			failed.append((fname, "implementing"))
			continue

		if out_fobj.tell() < 1 :
			print(here())
			failed.append((fname, "no_code_generated"))
			continue

		source = out_fobj.getvalue()

		source_dirs = set()
		for l in library.libs :
			if l.name in libs_used :
				for src_file in l.source_files :
					source_dirs.add(os.path.dirname(src_file))

		install_path = os.getcwd()
		blob_stream = StringIO()
		term_stream = StringIO()

		board_type = w.get_board()

		try :
			board_info = build.get_board_types()[board_type]
			variant = board_info["build.variant"] if "build.variant" in board_info else "standard" 
		except Exception :
			print(here())
			traceback.print_exc()
			failed.append((fname, "get_target_info"))
			continue


		try :
			rc, = build.build_source(board_type, source,
				aux_src_dirs=(
					(os.path.join(target_files_dir, "cores", "arduino"), False),
					(os.path.join(target_files_dir, "variants", variant), False),
	#				(os.path.join(install_path, "library", "arduino"), False),
				) + tuple( (path, True) for path in source_dirs ),#TODO derive from libraries used
				aux_idirs=[ os.path.join(install_path, "target", "arduino", "include") ],
				boards_txt=boards_txt,
				libc_dir=libc_dir,
	#			board_db={},
				ignore_file=None,#"amkignore",
	#			ignore_lines=( "*.cpp", "*.hpp", "*" + os.path.sep + "main.cpp", ), #TODO remove this filter with adding cpp support to build.py
				ignore_lines=( "*" + os.path.sep + "main.cpp", ),
	#			prog_port=None,
	#			prog_driver="avrdude", # or "dfu-programmer"
	#			prog_adapter="arduino", #None for dfu-programmer
				optimization="-Os",
				verbose=False,
				skip_programming=True,#False,
	#			dry_run=False,
				blob_stream=blob_stream,
				term=term_stream)
		except Exception :
			print(here())
			failed.append((fname, "build_failed"))
			continue



		succeeded.append((fname, ))

	finished = time.time()


	assert(len(failed) + len(succeeded) == len(files))

	print("")
	print("done in {:.3}s, {} of {} failed".format(finished - started, len(failed), len(files)))
	print("")
	print("failed files:")
	pprint(failed)


if __name__ == '__main__':
	main()


