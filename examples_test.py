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

	failed = []
	succeeded = []

	sink = StringIO()

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

		try :
			implement.implement_workbench(w, sheets, global_meta, ccodegen, core.KNOWN_TYPES, library, sink)#sys.stdout)
		except Exception :
			print(here())
			traceback.print_exc()
			failed.append((fname, "implementing"))
			continue

# ...

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


