#!/usr/bin/python

from serializer import unpickle_dfs_model
from implement import implement_workbench
import sys
import os
from dfs import Workbench
from serializer import unpickle_dfs_model, unpickle_workbench
from core import create_block_factory, KNOWN_TYPES
import ccodegen
#import fcodegen
from sys import version_info
if version_info.major == 3 :
	from io import StringIO
else :
	from StringIO import StringIO
import build

if __name__ == "__main__" :
#	import argparse
#	parser = argparse.ArgumentParser(description="bloced")
#	parser.add_argument("file", metavar="fname", type=str, nargs=1,
#                   help="input file")
#	args = parser.parse_args()
#	fname = args.file[0]

	fname = sys.argv[1]
	if len(sys.argv) == 4 :
		pass#TODO use output file

	if os.path.splitext(fname)[1].lower() == ".w" :
		w = Workbench(
			lib_dir=os.path.join(os.getcwd(), "library"),
			passive=True)
		blockfactory = w.blockfactory
		try :
			with open(fname, "rb") as f :
				unpickle_workbench(f, w)
		except :
			print("error loading workbench file")
			raise
#			exit(666)
		sheets = w.sheets
		global_meta = w.get_meta()
	else :
		blockfactory = create_block_factory(
				scan_dir=os.path.join(os.getcwd(), "library"))
		try :
			with open(fname, "rb") as f :
				model = unpickle_dfs_model(f, lib=blockfactory)
		except :
			print("error loading sheet file")
			exit(666)
		sheets = { "tsk" : model }
		global_meta = {}

	out_fobj = StringIO()
	implement_workbench(sheets, global_meta,
		ccodegen, KNOWN_TYPES, blockfactory, out_fobj)

	source = out_fobj.getvalue()
	print source

	blob_stream = StringIO()
	rc, = build.build_source(w.get_board(), source,
		aux_src_dirs=[
			("/usr/share/arduino/hardware/arduino/cores/arduino", False),
			(os.path.join(os.getcwd(), "library", "arduino"), False)
		],#TODO derive from libraries used
		boards_txt=build.BOARDS_TXT,
#		board_db={},
		ignore_file=None,#"amkignore",
		ignore_lines=[ "*.cpp", "*.hpp" ], #TODO remove this filter with adding cpp support to build.py
#		prog_port=None,
#		prog_driver="avrdude", # or "dfu-programmer"
#		prog_adapter="arduino", #None for dfu-programmer
		optimization="-Os",
		verbose=False,
		skip_programming=True,#False,
#		dry_run=False,
		blob_stream=blob_stream)

	blob = blob_stream.getvalue()
#	print blob

	board_info = w.get_board_types()[w.get_board()]
	prog_mcu = board_info["build.mcu"]
	rc = build.program("avrdude", w.get_port(), "arduino", prog_mcu, None,
		a_hex_blob=blob,
		verbose=True,
		dry_run=False)



