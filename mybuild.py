#!/usr/bin/python

from build import build
import sys
import os

if __name__ == "__main__" :
	boards = {
		"uno_dfu" : {
			"name" : "uno board dfu",
			"build.mcu" : "atmega8u2",
			"build.f_cpu" : "16000000L", "upload.maximum_size" : "7168"
		},
		"8u2@16M" : {
			"name" : "8u2@16M",
			"build.mcu" : "atmega8u2",
			"build.f_cpu" : "16000000L", "upload.maximum_size" : "7168"
		}
	}
#	AUX_SRC_DIR = "/usr/share/arduino/hardware/arduino/cores/arduino"
	rc, = build("uno_dfu", os.getcwd(),
		wdir_recurse = True,
		aux_src_dirs = [],#[ src_dir_t(AUX_SRC_DIR, False) ],
		boards_txt = None, #BOARDS_TXT,
		ignore_file = "amkignore",
		prog_port = None,#"/dev/ttyACM0",
		prog_driver = "dfu-programmer", # or "avrdude"
		prog_adapter = None, #"arduino", #None for dfu-programmer
		optimization = "-O0"#default "-Os",
		verbose = False,
		skip_programming = False,
		dry_run = True,
		board_db=boards)
	sys.exit(rc)


