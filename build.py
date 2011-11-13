
import sys
from sys import exit
import subprocess
import os
import tempfile
from functools import partial
import fnmatch

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


def __read_ignores(workdir) :
#TODO
#fnmatch.filter(names, pattern)
	return []

def build() :
	workdir = os.getcwd()

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
#	prog_port = "USB0"

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

