#!/usr/bin/python

from build import build, build_source
import sys
import os

if __name__ == "__main__" :
	boards = {
		"uno_dfu" : {
			"name" : "uno board dfu",
			"build.mcu" : "atmega8u2",
			"build.f_cpu" : "16000000L",
			"upload.maximum_size" : "7168"
		},
		"8u2@16M" : {
			"name" : "8u2@16M",
			"build.mcu" : "atmega8u2",
			"build.f_cpu" : "16000000L",
			"upload.maximum_size" : "7168"
		},
		"8u2@8M" : {
			"name" : "8u2@8M",
			"build.mcu" : "atmega8u2",
			"build.f_cpu" : "8000000L",
			"upload.maximum_size" : "7168"
		},
		"16u2@8M" : {
			"name" : "16u2@8M",
			"build.mcu" : "atmega16u2",
			"build.f_cpu" : "8000000L",
			"upload.maximum_size" : "16000"#XXX
		}
	}
#	AUX_SRC_DIR = "/usr/share/arduino/hardware/arduino/cores/arduino"
	x = 0
	if x == 0 :
		source = "void main() { for (;;); }"
		hexstream = None
		rc, = build_source("16u2@8M", source,
			aux_src_dirs = [],#[ src_dir_t(AUX_SRC_DIR, False) ],
			boards_txt = None, #BOARDS_TXT,
			ignore_file = "amkignore",
			prog_port = "/dev/ttyACM0",
			prog_driver = "avrdude",
			prog_adapter = None, #"arduino", #None for dfu-programmer
			optimization = "-Os",#default "-Os",
			verbose = True,
			skip_programming = True,
			dry_run = True,
			board_db=boards,
			blob_stream=hexstream)
	elif x == 1 :
		rc, = build("16u2@8M", os.getcwd(),
			wdir_recurse = True,
			aux_src_dirs = [],#[ src_dir_t(AUX_SRC_DIR, False) ],
			aux_src_files=[],
			boards_txt = None, #BOARDS_TXT,
			ignore_file = "amkignore",
			prog_port = "/dev/ttyACM0",
			prog_driver = "avrdude",
			prog_adapter = None, #"arduino", #None for dfu-programmer
			optimization = "-Os",#default "-Os",
			verbose = False,
			skip_programming = True,
			dry_run = True,
			board_db=boards)
	elif x == 2 :
		rc, = build("uno_dfu", os.getcwd(),
			wdir_recurse = True,
			aux_src_dirs = [],#[ src_dir_t(AUX_SRC_DIR, False) ],
			boards_txt = None, #BOARDS_TXT,
			ignore_file = "amkignore",
			prog_port = None,#"/dev/ttyACM0",
			prog_driver = "dfu-programmer", # or "avrdude"
			prog_adapter = None, #"arduino", #None for dfu-programmer
			optimization = "-O0",#default "-Os",
			verbose = False,
			skip_programming = False,
			dry_run = True,
			board_db=boards)
	sys.exit(rc)


