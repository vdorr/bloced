
from dfs import *
import os
import sys
import hparser
from collections import namedtuple
from itertools import groupby, count
from pprint import pprint

from implement import here, KNOWN_TYPES

# ------------------------------------------------------------------------------------------------------------

class JointProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Joint",
			[ Out(0, "y", C, 0, variadic=True), In(0, "x", C, 0) ],
			default_size=(8,8), category="Special")

class ConstProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Const",
			[ Out(0, "y", E, 0.5, type_name="<inferred>") ],
			default_size=(96,28), category="Special")

class DelayProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Delay", [ In(0, "x", E, 0.5), Out(0, "y", W, 0.5) ],
			category="Special")
		self.loop_break = True

class ProbeProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Probe", [ In(0, "x", W, 0.5) ],
			default_size=(96,28), category="Special", exe_name="probe")

class TapProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Tap", [ In(0, "x", W, 0.5) ],
			default_size=(96,28), category="Special")

class TapEndProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "TapEnd", [ Out(0, "y", E, 0.5) ],
			default_size=(96,28), category="Special")

class NoteProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Note", [ ],
			default_size=(96,28), category="Special")

class DelayInProto(BlockPrototype):

#	def __repr__(self) :
#		return "%s(%i)"%(self.__name, self.nr)

	def __init__(self) :
		BlockPrototype.__init__(self, "DelayIn", [ In(0, "x", W, 0.5) ])
#		self.nr = -1

class DelayOutProto(BlockPrototype):

#	def __repr__(self) :
#		return "%s(%i)"%(self.__name, self.nr)

	def __init__(self) :
		BlockPrototype.__init__(self, "DelayOut", [ Out(0, "y", E, 0.5) ])
#		self.nr = -1

class SignalProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Signal", [ Out(0, "y", E, 0.5) ],
			default_size=(48,48), category="Special")

class SysRqProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "SysRq",
			[ In(-1, "en", W, 0.25),
			  In(-2, "nr", W, 0.5),
			  In(-3, "x", W, 0.75, variadic=True),
			  Out(-3, "eno", E, 0.25),
			  Out(-1, "rc", E, 0.5),
			  Out(-2, "y", E, 0.75, variadic=True) ],
			exe_name="sysrq",
			default_size=(64,80), category="Special")

class InputProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Input", [ Out(0, "x", E, 0.5) ],
			default_size=(96,28), category="Special")

class OutputProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Output", [ In(0, "y", W, 0.5) ],
			default_size=(96,28), category="Special")

# ------------------------------------------------------------------------------------------------------------

class SBP(BlockPrototype) :
	def __init__(self, type_name, category, terms, exe_name=None, commutative=False, pure=False) :
		BlockPrototype.__init__(self, type_name, terms,
			exe_name=type_name if not exe_name else exe_name,
			category=category,
			commutative=commutative,
			pure=pure)

# ------------------------------------------------------------------------------------------------------------

class UnaryOp(BlockPrototype) :
	def __init__(self, type_name, category, exe_name=None) :
		BlockPrototype.__init__(self,
			type_name,
			[ In(0, "a", W, .5), Out(0, "y", E, .5) ],
			exe_name=type_name if not exe_name else exe_name,
			category=category,
			pure=True)

# ------------------------------------------------------------------------------------------------------------

class BinaryOp(BlockPrototype) :
	def __init__(self, type_name, category, exe_name=None, commutative=False) :
		BlockPrototype.__init__(self,
			type_name,
			[ In(0, "a", W, .33), In(0, "b", W, .66), Out(0, "y", E, .5) ],
			exe_name=type_name if not exe_name else exe_name,
			category=category,
			commutative=commutative,
			pure=True)

# ------------------------------------------------------------------------------------------------------------

#TODO TODO TODO
class StatefulBP(BlockPrototype) :
	def __init__(self, type_name, terms, exe_name=None) :
		BlockPrototype.__init__(self, type_name, terms,
			exe_name=type_name if not exe_name else exe_name)
#TODO TODO TODO

# ----------------------------------------------------------------------------

class CFunctionProto(BlockPrototype):
	pass
#	def __init__(self) :
#		BlockPrototype.__init__(self, "CFunction", [], category="External")

# ----------------------------------------------------------------------------

class MacroProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Macro", [], category="External")

# ----------------------------------------------------------------------------

class FunctionProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "FunctionBlock", [], category="External")

# ----------------------------------------------------------------------------

def load_macro(filename) :
#	print "load_macro:", filename
	return None

# ----------------------------------------------------------------------------

VMEX_SIG = "_VM_EXPORT_"

#known_types = {
#	"vm_char_t" : (None, ), #XXX XXX XXX
#	"vm_word_t" : (1, ),
#	"vm_dword_t" : (2, ),
#	"vm_float_t" : (2, ),
#	"void" : (0, ),
#}

def is_vmex_line(s) :
	ln = s.strip()
#	print(s.__class__)
	if not ln.startswith(VMEX_SIG) :
		return None
	return ln

def parse_vmex_line(s) :
	hparser.__hparser_linesep = "\n" #XXX XXX XXX XXX XXX
	tokens = hparser.tokenize(s)
#	print "parse_vmex_line:", tokens
	if not tokens :
		return None
	ret_type, name, args_list = hparser.parse_decl(tokens)
	return ret_type, name, args_list

term_type = namedtuple("term", (
#	"arg_index",
	"name",
#	"side", "pos",
	"direction", "variadic", "commutative", "type_name"))

def vmex_arg(a, known_types) :
	sig, name = a
#	print "vmex_arg", a

#	TermModel arg_index, name, side, pos, direction, variadic, commutative, type_name=None
#	name,
	direction = OUTPUT_TERM if "*" in sig else INPUT_TERM
	variadic = False
	commutative = False
	
	(type_name, ) = [ tp for tp in sig if tp in known_types ]
	return term_type(name, direction, variadic, commutative, type_name)

def extract_exports(src_str, known_types) :
	src_lines = src_str.split("\n")
#	pprint(src_lines)
	exports = [ parse_vmex_line(ln) for ln in
		[ is_vmex_line(ln) for ln in src_lines ] if ln != None ]

#	print("extract_exports: ", len(exports))
	vmex_funcs = []

	for ret_type, name, args_list in exports :

#		print ret_type, name, args_list

		if ret_type[0] != VMEX_SIG :
			continue # should not happen
		vmex_ret_type = None
		for tp in ret_type :
			if tp in known_types :
				vmex_ret_type = tp
		outputs = [ (a_sig, a_name) for a_sig, a_name in args_list if "*" in a_sig ]
		if outputs :
			assert(vmex_ret_type == "void")
		inputs = [ a for a in args_list if not a in outputs ]
		assert(set(outputs+inputs)==set(args_list))

		terms_in = [ vmex_arg(a, known_types) for a in inputs ]
		if outputs :
			terms_out = [ vmex_arg(a, known_types) for a in outputs ]
		elif ret_type[-1] != "void" :
			terms_out = [ vmex_arg((ret_type, "out"), known_types) ]
		else :
			terms_out = []
#		print name, ret_type#, terms_in, terms_out

		#TermModel arg_index, name, side, pos, direction, variadic, commutative, type_name=None
		vmex_funcs.append((name, (terms_in, terms_out)))

	return vmex_funcs

def extract_vmex(fname, known_types) :
	srcf = open(fname, "r")
	src_str = srcf.read()
	srcf.close()
	return extract_exports(src_str, known_types)

from dfs import TERM_SIZE, MIN_BLOCK_WIDTH, MIN_BLOCK_HEIGHT, guess_block_size

def __layout_terms(all_terms_count, term_count) : #TODO move to dfs
	step = 1.0 / (all_terms_count + 1)
	term_positions = [ (i + 1) * step for i in range(term_count) ]
	return term_positions

def block_layout(in_term_count, out_term_count) :
	all_terms_count = max(in_term_count, out_term_count)
	inputs = __layout_terms(all_terms_count, in_term_count)
	outputs = __layout_terms(all_terms_count, out_term_count)
	width, height = guess_block_size([], [], inputs, outputs)
	return width, height, inputs, outputs

def __cmod_create_proto(lib_name, export) :

	block_name, (terms_in, terms_out) = export

	width, height, in_terms_pos, out_terms_pos = block_layout(len(terms_in), len(terms_out))
#	print "__cmod_create_proto: block_layout=", xxxx

	#arg_index, name, side, pos, type_name=None, variadic=False, commutative=False
	inputs = [ In(-i, name, W, pos,
			type_name=type_name, variadic=variadic, commutative=commutative)
		for (name, direction, variadic, commutative, type_name), pos, i
			in zip(terms_in, in_terms_pos, count()) ]
	outputs = [ Out(-i, name, E, pos,
			type_name=type_name, variadic=variadic, commutative=commutative)
		for (name, direction, variadic, commutative, type_name), pos, i
			in zip(terms_out, out_terms_pos, count()) ]

	proto = CFunctionProto(block_name,
			inputs + outputs,
			exe_name=block_name,
			default_size=(width, height),
			category=lib_name)
	return proto

#def __cmod_name_from_fname(fname) :
#	return None

HEADER_EXTS = ("h", "hpp")

def __is_header(fname) :
	ext = fname.split(os.path.extsep)[-1]
	return ext.lower() in HEADER_EXTS

def load_c_module(lib_name, input_files) :
#	print "load_c_module:", input_files
#	exports = [ (fn, extract_vmex(fn)) for fn in input_files ]
	header = [ fn for fn in input_files if __is_header(fn) ][-1]
	exports = extract_vmex(header, KNOWN_TYPES)
#	print("library '%s' exports %i functions" % (lib_name, len(exports)))
#	pprint(exports)
#TODO now produce prototypes
	protos = [ __cmod_create_proto(lib_name, export) for export in exports ]
	return protos

# ------------------------------------------------------------------------------------------------------------

class BasicBlocksFactory(object) :


	def load_library(self, basedir) :
#		print basedir
		try :
			dirname, dirnames, filenames = os.walk(basedir).next()
		except :
			print("load_library: failed to scan ", basedir)
			return (False, )

		lib_name = os.path.split(dirname)[-1]

#		print lib_name, dirname, dirnames, filenames

		MY_FILE_EXTENSION = "bloc"#XXX

		for f in filenames :
#			fname_split = f.split(os.path.extsep)
#			ext = fname_split[-1]
#			fname = fname_split[:-1]
			ext = f.split(os.path.extsep)[-1]
			fname = f[0:(len(f)-len(ext)-len(os.path.extsep))]
			if ext == MY_FILE_EXTENSION :
				try :
					blocks = load_macro(f)
				except :
					print("failed to load " + f)
				else :
					if blocks == None :
						continue #XXX
					self.__blocks += blocks
			elif ext == "c" and (fname + os.path.extsep + "h") in filenames : #XXX too naive!
				try :
					blocks = load_c_module(lib_name, [os.path.join(dirname, f),
						os.path.join(dirname, fname + os.path.extsep + "h")])
				except :
					print("failed to load " + f)
					raise
				else :
					if blocks == None :
						continue #XXX
					self.__blocks += blocks
		for d in dirnames :
			self.load_library(os.path.join(dirname, d))

		self.__blocks += []

		return (True, )


	def get_block_by_name(self, type_name) :
		p = list(islice(dropwhile(lambda proto: proto.type_name != type_name,
			self.__blocks), 0, 1))
		if not p :
			raise Exception("type_name '" + type_name + "' not found")
		return p[0]#.__class__()


	block_list = property(lambda self: self.__blocks)


	def __init__(self, scan_dir=None) :
#		print("factory init scan_dir=", scan_dir, id(self), here(10))
		self.__blocks = [
			JointProto(),
			ConstProto(),
			DelayProto(),
			ProbeProto(),
			TapProto(),
			TapEndProto(),
#			SignalProto(),
#			NoteProto(),
			SysRqProto(),
			InputProto(),
			OutputProto(),
			SBP("Sink", "Special", [ In(-1, "", W, .5, type_name="<infer>") ], pure=True),

			BinaryOp("xor", "Logic", commutative=True),
			BinaryOp("or", "Logic", commutative=True),
			BinaryOp("nor", "Logic", commutative=True),
			BinaryOp("and", "Logic", commutative=True),
			BinaryOp("nand", "Logic", commutative=True),
			UnaryOp("not", "Logic"),

			BinaryOp("add", "Arithmetic", commutative=True),
			BinaryOp("sub", "Arithmetic", commutative=False),
			BinaryOp("mul", "Arithmetic", commutative=True),
			BinaryOp("div", "Arithmetic", commutative=False),
			BinaryOp("mod", "Arithmetic", commutative=False),
			SBP("divmod", "Arithmetic", [ In(-1, "n", W, .33), In(-1, "d", W, .66),
				Out(-1, "q", E, .33), Out(-2, "r", E, .66) ], pure=True),
			BinaryOp("lt", "Arithmetic", commutative=False),
			BinaryOp("gt", "Arithmetic", commutative=False),
			BinaryOp("eq", "Arithmetic", commutative=False),
			BinaryOp("lte", "Arithmetic", commutative=False),
			BinaryOp("gte", "Arithmetic", commutative=False),

#			SBP("load", "Memory", [ ]),
#			SBP("store", "Memory", [ ]),
#			SBP("load_nv", "Memory", [ ]),
#			SBP("store_nv", "Memory", [ ]),

			SBP("di", "Process IO", [ In(0, "nr", W, .5, type_name="vm_word_t"),
				Out(0, "y", E, .5, type_name="vm_word_t") ], exe_name="io_di"),
			SBP("do", "Process IO", [ In(-1, "nr", W, .33, type_name="vm_word_t"),
				In(-2, "x", W, .66, type_name="vm_word_t") ], exe_name="io_do"),
		]
		if scan_dir :
			self.load_library(scan_dir)

# ------------------------------------------------------------------------------------------------------------

def create_block_factory(**args) :
	return BasicBlocksFactory(**args)

# ----------------------------------------------------------------------------

if __name__ == "__main__" :
#	OUTPUT_TERM, INPUT_TERM = 666, 667
	if len(sys.argv) > 1 :
		if sys.argv[1] == "librariantest" :
			if len(sys.argv) == 2 :
				source = "iowrap.h"
			else :
				source = sys.argv[2]
			srcf = open(source, "r")
			srcs = srcf.readlines()
			srcf.close()
			exports = extract_exports(srcs)
		elif sys.argv[1] == "libscantest" :
# python core.py libscantest
			if len(sys.argv) == 2 :
				lib_dir = "library"
			else :
				lib_dir = sys.argv[2]
			librarian = BasicBlocksFactory()
			librarian.load_library(os.path.join(os.getcwd(), lib_dir))

			for cat, b_iter in groupby(librarian.block_list, lambda b: b.category) :
				print(cat)
				for proto in b_iter :
					print("\t" + proto.type_name)

# ----------------------------------------------------------------------------

