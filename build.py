
from sys import exit
import subprocess
import os
import tempfile

# ----------------------------------------------------------------------------

#class __sink(object) :
#	def write(self, s) :
#		self.__data += s
#	def __init__(self) :
#		self.__data = ""

#		p = subprocess.Popen(["avr-size", a_out], bufsize=0, executable=None, stdin=None, stdout=subprocess.PIPE,
#			stderr=subprocess.PIPE, preexec_fn=None, close_fds=False, shell=False,
#		cwd=os.getcwd(), env=None, universal_newlines=False, startupinfo=None, creationflags=0)


def build() :
	workdir = os.getcwd()

#	a_out_f = tempfile.NamedTemporaryFile()
#	a_hex_f = tempfile.NamedTemporaryFile()
#	a_out = a_out_f.name
#	a_hex = a_hex_f.name

	a_out, a_hex = "a.out", "a.hex"
	i_dirs = []#[ "/usr/lib/avr", "/usr/lib/avr/include", "/usr/lib/avr/util", "/usr/lib/avr/compat" ]
	l_libs = []#[ "/usr/lib/avr/lib/libc.a" ]

	optimization = "-Os"
	mcu = "atmega328"
	f_cpu = 16000000
	
	prog_mcu = "m328p"
	prog_port = "/dev/ttyACM0"

	gcc_args = i_dirs + l_libs + [ optimization, "-mmcu=" + mcu, "-DF_CPU=%i" % f_cpu, "-o", a_out ]

	try :
		p = subprocess.Popen(["avr-gcc"] + gcc_args,
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			cwd=workdir)
	except :
		print("failed to execute avr-gcc")
	else :
		(stdoutdata, stderrdata) = p.communicate()
		if p.returncode == 0 :
			print("compiled")
		else :
			print("failed to execute avr-gcc")

	try :
		p = subprocess.Popen(["avr-size", a_out],
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			cwd=workdir)
	except :
		print("failed to execute avr-size")
	else :
		(stdoutdata, stderrdata) = p.communicate()
		if p.returncode == 0 :
			head, val = stdoutdata.split(os.linesep)[0:2]
			sizes = dict(zip(head.split(), val.split()))
			print("memory usage: flash %iB, ram %iB" %
				(int(sizes["text"]), int(sizes["data"])+int(sizes["bss"])))
		else :
			print("failed to execute avr-size")

	try :
		p = subprocess.Popen(
			["avr-objcopy", "-j", ".text", "-j", ".data" "-O" "ihex", a_out, a_hex],
			cwd=workdir)
	except :
		print("failed to execute avr-objcopy")
	else :
		p.communicate()
		if p.returncode == 0 :
			pass
		else :
			print("failed to execute avr-objcopy")


	try :
		p = subprocess.Popen(
			["avrdude", "-q", "-n", "-c arduino", "-P " + prog_port, "-m " + prog_mcu, "-U flash:w:" + a_hex + ":i"],
			cwd=workdir)
	except :
		print("failed to run avrdude")
	else :
		p.communicate()
		if p.returncode == 0 :
			pass
		else :
			print("failed to run avrdude")

	exit(666)

# ----------------------------------------------------------------------------

if __name__ == "__main__" :
	build()

# ----------------------------------------------------------------------------

