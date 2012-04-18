
import dfs
import os
import sys
import hparser
from collections import namedtuple
from itertools import groupby, count, islice
from pprint import pprint
import serializer
from utils import here

# ------------------------------------------------------------------------------------------------------------

#XXX XXX XXX

#TODO fetch type informations from some "machine support package"

type_t = namedtuple("type_t", [ "size_in_words", "size_in_bytes", "priority", ])

#type_name : (size_in_words, size_in_bytes, priority)
KNOWN_TYPES = {
	"<inferred>" : None, #XXX OH MY GOD!!!!!!!!
	"vm_char_t" : type_t(1, 1, 0), #TODO
	"vm_word_t" : type_t(1, 2, 1),
	"vm_dword_t" : type_t(2, 4, 2),
	"vm_float_t" : type_t(2, 4, 3),
	"void" : None,
}

#XXX XXX XXX
# ------------------------------------------------------------------------------------------------------------

class BlockPrototype(object) :

	# to be shown in bloced
	type_name = property(lambda self: self.__type_name)

	# to be used in code to execute block
	exe_name = property(lambda self: self.__exe_name)

	terms = property(lambda self: self.__terms)

	inputs = property(lambda self: [ t for t in self.__terms if t.direction == dfs.INPUT_TERM ] )

	outputs = property(lambda self: [ t for t in self.__terms if t.direction == dfs.OUTPUT_TERM ] )
	
	category = property(lambda self: self.__category)
	
	default_size = property(lambda self: self.__default_size)

	commutative = property(lambda self: self.__commutative)

	pure = property(lambda self: self.__pure)

	values = property(lambda self: self.__values)

	library = property(lambda self: self.__library)

	def __init__(self, type_name, terms,
			exe_name=None,
			default_size=(64,64),
			category="all",
			commutative=False,
			pure=False,
			values=None,
			library=None) :
		self.__category = category
		#TODO return self.type_name if not self.exe_name else self.exe_name
		self.__type_name = type_name
		self.__terms = terms
		self.__default_size = default_size
		self.__exe_name = exe_name
		self.__commutative = commutative
		self.__pure = pure
		self.__values = values
		self.__library = library

# ------------------------------------------------------------------------------------------------------------

class JointProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Joint",
			[ dfs.Out(0, "y", dfs.C, 0, variadic=True), dfs.In(0, "x", dfs.C, 0) ],
			default_size=(8,8), category="Special")


class ConstProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Const",
			[ dfs.Out(0, "y", dfs.E, 0.5, type_name="<inferred>") ],
			default_size=(96,28), category="Special",
			values=[("Value", None)])


class DelayProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Delay", [ dfs.In(0, "x", dfs.E, 0.5), dfs.Out(0, "y", dfs.W, 0.5) ],
			category="Special",
			values=[("Default", None)])
		self.loop_break = True


class ProbeProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Probe", [ dfs.In(0, "x", dfs.W, 0.5) ],
			default_size=(96,28), category="Special", exe_name="probe")


class TapProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Tap", [ dfs.In(0, "x", dfs.W, 0.5) ],
			default_size=(96,28), category="Special",
			values=[("Name", None)])


class TapEndProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "TapEnd", [ dfs.Out(0, "y", dfs.E, 0.5) ],
			default_size=(96,28), category="Special",
			values=[("Name", None)])


class NoteProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Note", [ ],
			default_size=(96,28), category="Special",
			values=[("Text", "")])


class DelayInProto(BlockPrototype):

#	def __repr__(self) :
#		return "%s(%i)"%(self.__name, self.nr)

	def __init__(self) :
		BlockPrototype.__init__(self, "DelayIn", [ dfs.In(0, "x", dfs.W, 0.5) ])
#		self.nr = -1


class DelayOutProto(BlockPrototype):

#	def __repr__(self) :
#		return "%s(%i)"%(self.__name, self.nr)

	def __init__(self) :
		BlockPrototype.__init__(self, "DelayOut", [ dfs.Out(0, "y", dfs.E, 0.5) ])
#		self.nr = -1


class SignalProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Signal", [ dfs.Out(0, "y", dfs.E, 0.5) ],
			default_size=(48,48), category="Special")


class SysRqProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "SysRq",
			[ dfs.In(-1, "en", dfs.W, 0.25),
			  dfs.In(-2, "nr", dfs.W, 0.5),
			  dfs.In(-3, "x", dfs.W, 0.75, variadic=True),
			  dfs.Out(-3, "eno", dfs.E, 0.25),
			  dfs.Out(-1, "rc", dfs.E, 0.5),
			  dfs.Out(-2, "y", dfs.E, 0.75, variadic=True) ],
			exe_name="sysrq",
			default_size=(64,80), category="Special")


class InputProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Input", [ dfs.Out(0, "x", dfs.E, 0.5) ],
			default_size=(96,28), category="Special",
			values=[("Name", None)])


class OutputProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Output", [ dfs.In(0, "y", dfs.W, 0.5) ],
			default_size=(96,28), category="Special",
			values=[("Name", None)])


class PipeProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Pipe", [ dfs.In(0, "x", dfs.W, 0.5) ],
			default_size=(96,28), category="Special",
			values=[("Name", None), ("Default", None)])


class PipeEndProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "PipeEnd", [ dfs.Out(0, "y", dfs.E, 0.5) ],
			default_size=(96,28), category="Special",
			values=[("Name", None)])

#TODO
class GlobalWriteProto(BlockPrototype):
	def __init__(self, type_name) :
		BlockPrototype.__init__(self, "GlobalWrite",
			[ dfs.In(0, "x", dfs.W, 0.5, type_name=type_name) ],
			default_size=(96,28),
			values=[("Name", None), ("Sync", None)])


class GlobalReadProto(BlockPrototype):
	def __init__(self, type_name) :
		BlockPrototype.__init__(self, "GlobalRead",
			[ dfs.Out(0, "y", dfs.E, 0.5, type_name=type_name) ],
			default_size=(96,28),
			values=[("Name", None), ("Sync", None)])


class FunctionCallProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "FunctionCall", [],
			values=[("Name", None)])


class MuxProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "mux", [
			dfs.In(-1, "x", dfs.W, .25, type_name="<inferred>"),#XXX should be binary
			dfs.In(-2, "a", dfs.W, .5, type_name="<inferred>"),
			dfs.In(-3, "b", dfs.W, .75, type_name="<inferred>"),
			dfs.Out(-1, "q", dfs.E, .5, type_name="<inferred>"), ],
			pure=True, category="Special")


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
			[ dfs.In(0, "a", dfs.W, .5), dfs.Out(0, "y", dfs.E, .5) ],
			exe_name=type_name if not exe_name else exe_name,
			category=category,
			pure=True)

# ------------------------------------------------------------------------------------------------------------

class BinaryOp(BlockPrototype) :
	def __init__(self, type_name, category, exe_name=None, commutative=False) :
		BlockPrototype.__init__(self,
			type_name,
			[ dfs.In(0, "a", dfs.W, .33), dfs.In(0, "b", dfs.W, .66), dfs.Out(0, "y", dfs.E, .5) ],
			exe_name=type_name if not exe_name else exe_name,
			category=category,
			commutative=commutative,
			pure=True)

# ------------------------------------------------------------------------------------------------------------

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


VMEX_SIG = "_VM_EXPORT_"


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


term_type_t = namedtuple("term", (
#	"arg_index",
	"name",
#	"side", "pos",
	"direction", "variadic", "commutative", "type_name"))


def vmex_arg(a, known_types) :
	sig, name = a
#	print "vmex_arg", a

#	TermModel arg_index, name, side, pos, direction, variadic, commutative, type_name=None
#	name,
	direction = dfs.OUTPUT_TERM if "*" in sig else dfs.INPUT_TERM
	variadic = False
	commutative = False
	
	(type_name, ) = [ tp for tp in sig if tp in known_types ]
	return term_type_t(name, direction, variadic, commutative, type_name)


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
	inputs = [ dfs.In(-i, name, dfs.W, pos,
			type_name=type_name, variadic=variadic, commutative=commutative)
		for (name, direction, variadic, commutative, type_name), pos, i
			in zip(terms_in, in_terms_pos, count()) ]
	outputs = [ dfs.Out(-i, name, dfs.E, pos,
			type_name=type_name, variadic=variadic, commutative=commutative)
		for (name, direction, variadic, commutative, type_name), pos, i
			in zip(terms_out, out_terms_pos, count()) ]

	proto = CFunctionProto(block_name,
			inputs + outputs,
			exe_name=block_name,
			default_size=(width, height),
			category=lib_name,
			library=lib_name)
	return proto


#def __cmod_name_from_fname(fname) :
#	return None


HEADER_EXTS = ("h", "hpp")


def __is_header(fname) :
	ext = fname.split(os.path.extsep)[-1]
	return ext.lower() in HEADER_EXTS


#c_lib_data_t = namedtuple("c_lib_data", ("name", "path", "headers", "blocks", ))


def load_c_module(lib_name, header) :
#TODO use directory path or single file instead of list of files
#	header_list = [ fn for fn in input_files if __is_header(fn) ]
#	assert(len(header_list)==1)
#	header, = header_list
	exports = extract_vmex(header, KNOWN_TYPES)
	protos = [ __cmod_create_proto(lib_name, export) for export in exports ]
	return protos#TODO c_lib_data_t(lib_name)


#def scan_c_module(lib_name, path, input_files) :

#	header_list = [ fn for fn in input_files if __is_header(fn) ]
#	exports = extract_vmex(header, KNOWN_TYPES)
#	protos = [ __cmod_create_proto(lib_name, export) for export in exports ]
#	return lib_info_t(
#		path=path,
#		files=header_list,#XXX what about sources?
#		using_types=None)


# ------------------------------------------------------------------------------------------------------------


def guess_block_size(terms_N, terms_S, terms_W, terms_E) :
	mc_width = max([ len(terms_W) + 1, len(terms_E) + 1 ]) * dfs.TERM_SIZE
	mc_width = mc_width if mc_width >= dfs.MIN_BLOCK_WIDTH else dfs.MIN_BLOCK_WIDTH
	mc_height = max([ len(terms_N) + 1, len(terms_S) + 1 ]) * dfs.TERM_SIZE
	mc_height = mc_height if mc_height >= dfs.MIN_BLOCK_HEIGHT else dfs.MIN_BLOCK_HEIGHT
	return mc_width, mc_height


def __mc_term_info(model, tb) :
	(x, y), _ = tb.get_term_and_lbl_pos(tb.terms[0], 0, 0, 0)
	return (tb, (tb.left+x, tb.top+y))


#def __mc_assign_side(tb, k, w, u, x, y) :
#	sides = {
#		(True, True) : N,
#		(False, False) : S,
#		(True, False) : W,
#		(False, True) : E
#	}
#	print tb, x, y,  y>(k * x), y>((-k * (x-w))+u)
#	return sides[y>(k * x), y>((-k * (x-w))+u)]

def __mc_assign_side(tb, center_x, center_y, x, y) :
	sides = {
		(True, True) : dfs.S,
		(True, False) : dfs.N,
		(False, True) : dfs.E,
		(False, False) : dfs.W
	}
	side = tb.terms[0].get_side(tb)
	vertical = side in (dfs.N, dfs.S)
#	print tb, x, y,  y>(k * x), y>((-k * (x-w))+u)
	return sides[vertical, y > center_y if vertical else x > center_x ]


def __mc_assign_positions(term_sides, side) :
	assert(side in (dfs.N, dfs.S, dfs.W, dfs.E))
	terms = [ (tb, sd, y if side in (dfs.N, dfs.S) else x)
		for tb, sd, (x, y) in term_sides if sd == side ]
	terms.sort(key=lambda tb_sd_y: tb_sd_y[2])#(tb, sd, y): y)
	step = 1.0 / (len(terms) + 1)
	term_positions = [ (tb, sd, (i + 1) * step) for (tb, sd, p), i in zip(terms, count()) ]
#	print "step=", step, "term_positions=", term_positions
	return term_positions


def try_mkmac(model) :
#	inputs = [ b for b in model.blocks if isinstance(b.prototype, InputProto) ]
#	outputs = [ b for b in model.blocks if isinstance(b.prototype, OutputProto) ]

	terms = [ __mc_term_info(model, b)
		for b in model.blocks if b.prototype.__class__ in (InputProto, OutputProto) ]
	print("try_mkmac:", terms)

	def __sizes(rct0, rct1) :
		(l0, t0, r0, b0), (l1, t1, r1, b1) = rct0, rct1
		return (l1 if l1 < l0 else l0,
			t1 if t1 < t0 else t0,
			r1 if r1 > r0 else r0,
			b1 if b1 > b0 else b0)
	if terms :
		#TODO use mathutils.bounding_rect
		(l, t, r, b) = reduce(__sizes, [ (x, y, x, y) for _, (x, y) in terms ])
	else :
		(l, t, r, b) = (0, 0, dfs.MIN_BLOCK_WIDTH, dfs.MIN_BLOCK_HEIGHT)
#	(l, t, r, b) = (l-1, t-1, r+1, b+1)

#	k = float(b) / float(r)# (l,t) (r,b)
##	k = float(b-t) / float(r-l)# (l,t) (r,b)
##	kb = float(t-b) / float(r-l) # (l,b) (r,t)
	print("try_mkmac: l, t, r, b, w,h=", l, t, r, b, r-l, b-t)

	term_sides = [ (tb, __mc_assign_side(tb, l+((r-l)/2), t+((b-t)/2), x, y), (x, y)) for tb, (x, y) in terms]
#	xxx = [ (tb, __mc_assign_side(tb, k, (r-l)/2, (b-t), x, y)) for tb, (x, y) in terms]
	print("try_mkmac: sides=", term_sides)

#	term_WE = [ (tb, side) for tb, side in term_sides if side in (W, E) ]
#	term_NS = [ (tb, side) for tb, side in term_sides if side in (N, S) ]

#	term_W = [ (tb, side, x, y) for tb, side, (x, y) in term_sides if side == W ]
#	term_E = [ (tb, side, x, y) for tb, side, (x, y) in term_sides if side == E ]
#	term_S = [ (tb, side, x, y) for tb, side, (x, y) in term_sides if side == S ]
#	term_N = [ (tb, side, x, y) for tb, side, (x, y) in term_sides if side == N ]

#	term_W = [ (tb, side, y) for tb, side, (x, y) in term_sides if side == W ]
#	term_W = sorted(term_W, key=lambda (tb, side, y): y)
#	step = 1.0 / (len(term_W) + 1)
#	term_positions = [ (tb, side, (i + 1) * step) for (tb, side, p), i in zip(term_W, count()) ]
#	print "step=", step, "term_positions=", term_positions

#	term_E = [ (tb, side, y) for tb, side, (x, y) in term_sides if side == E ]
#	term_S = [ (tb, side, x) for tb, side, (x, y) in term_sides if side == S ]
#	term_N = [ (tb, side, x) for tb, side, (x, y) in term_sides if side == N ]

	terms_W = __mc_assign_positions(term_sides, dfs.W)
	terms_E = __mc_assign_positions(term_sides, dfs.E)
	terms_S = __mc_assign_positions(term_sides, dfs.S)
	terms_N = __mc_assign_positions(term_sides, dfs.N)

	mc_width = max([ len(terms_W) + 1, len(terms_E) + 1 ]) * dfs.TERM_SIZE
	mc_width = mc_width if mc_width >= dfs.MIN_BLOCK_WIDTH else dfs.MIN_BLOCK_WIDTH
	mc_height = max([ len(terms_N) + 1, len(terms_S) + 1 ]) * dfs.TERM_SIZE
	mc_height = mc_height if mc_height >= dfs.MIN_BLOCK_HEIGHT else dfs.MIN_BLOCK_HEIGHT

	mc_width, mc_height = guess_block_size(terms_N, terms_S, terms_W, terms_E)

	term_positions = terms_N + terms_S + terms_W + terms_E

	print("term_positions=", mc_width, mc_height, term_positions)

	mc_name = None # TODO
	terminals = None

	return mc_width, mc_height, mc_name, terminals
#	graph, delays = make_dag(model, {})
#	pprint(graph)


def is_macro_name(s) :
	return s.strip().startswith("@macro:")


#def load_macroes_from_workbench(w, input_files) :
#	for (name, sheet) in w.sheets.items() :
#		if is_macro_name(name) :
#			print(name, sheet)
#	return []


#def load_workbench_libraryOLD(lib_name, input_files) :

#	fname, = input_files
#	w = dfs.Workbench(
#		lib_dir=os.path.join(os.getcwd(), "library"),
#		passive=True,
#		do_create_block_factory=False)
#	blockfactory = w.blockfactory
#	try :
#		with open(fname, "rb") as f :
#			serializer.unpickle_workbench(f, w)
#			blocks = load_macroes_from_workbench(w, input_files)
#	except Exception as e :
#		print(here(), "error loading workbench file", fname, e)
#		return None
#	else :
#		return blocks


def load_workbench_library(lib_name, input_files) :
	"""
	lib_name - full library name, example 'logic.flipflops'
	"""
	fname, = input_files

##XXX
#	return []
##XXX

#	w = dfs.Workbench(
#		lib_dir=os.path.join(os.getcwd(), "library"),
#		passive=True,
#		do_create_block_factory=False)

#	with open(fname, "rb") as f :
##		version, meta, resources = serializer.unpickle_workbench_data(f)
#		serializer.unpickle_workbench(f, w)

##	try_mkmac(model)

#	print here(), w.sheets
#	return []






	try :
		with open(fname, "rb") as f :
			version, meta, resources = serializer.unpickle_workbench_data(f)
	except Exception as e :
		print(here(), "error loading workbench file", fname, e)
		return None

	used_libs = set()
#XXX type_names must be unique -> need to extend them with library path, including c modules
	for r_type, r_version, r_name, resrc in resources :
		if (r_type == serializer.RES_TYPE_SHEET and
				r_version == serializer.RES_TYPE_SHEET_VERSION and
				is_macro_name(r_name) ) :
			types, struct, meta = resrc
			for nr, block_type in types :
#				print nr, block_type
				lib_name, type_name = split_full_type_name(block_type)
				if lib_name :
					print(here(), nr, lib_name, type_name)
					used_libs.update((lib_name,))
#				print fname, r_name

	print(here(), used_libs)

	return []#blocks





def get_workbench_dependencies(fname) :
	"""
	return set of block types immediately needed by workbench file fname
	these block types may have other dependencies
	"""
	try :
		with open(fname, "rb") as f :
			version, meta, resources = serializer.unpickle_workbench_data(f)
	except Exception as e :
		print(here(), "error loading workbench file", fname, e)
		return None

	used_types = set()
#XXX type_names must be unique -> need to extend them with library path, including c modules
	for r_type, r_version, r_name, resrc in resources :
		if (r_type == serializer.RES_TYPE_SHEET and
				r_version == serializer.RES_TYPE_SHEET_VERSION and
				is_macro_name(r_name) ) :
			types, struct, meta = resrc
			for nr, block_type in types :
#				print nr, block_type
				lib_name, type_name = split_full_type_name(block_type)
				if lib_name :
#					print(here(), nr, lib_name, type_name)
					used_types.update((block_type,))
#				print fname, r_name

#	print(here(), used_types)

	return used_types



#-------------------------------------------------------------------------------------------------------------


be_lib_block_t = namedtuple("be_lib_item",  ("library", "file_path", "src_type", "name", "block_name"))


be_library_t = namedtuple("be_library", ("name", "path", "allowed_targets", "include_files", "items"))


def split_full_type_name(full_type) :
	type_name_parts = full_type.split(".")
	type_name = type_name_parts[-1]
	lib_name = ".".join(type_name_parts[:-1])
	return lib_name, type_name


def read_be_lib_file(path) :
	pass


def lib_name_from_path(lib_basedir, path) :
	libname = []
	relpath = os.path.relpath(path, lib_basedir)
	while not relpath in ("", os.path.pardir, os.path.curdir) :
		relpath, libname_part = os.path.split(relpath)
		libname.insert(0, libname_part)
	return ".".join(libname)


def __lib_path_and_name(root, lib_base_name, f) :
	fbasename, ext = os.path.splitext(f)
	ext = ext.lstrip(os.path.extsep).lower()
	filepath = os.path.join(root, f)
	lib_name = lib_base_name
	if ext in ("bloc", "w") :
		lib_name = ".".join((lib_base_name, fbasename))
	return ext, lib_name, filepath


def read_lib_dir(lib_basedir, path, peek=False) :
	"""
	load libraries from path, contained in lib_basedir, both have to be absolute paths
	"""

	(root, dirnames, filenames), = tuple(islice(os.walk(path), 1))

	lib_base_name = lib_name_from_path(lib_basedir, path)

	items = []
	include_files = []
	blocks = tuple()

	sublibs = tuple(__lib_path_and_name(root, lib_base_name, f) for f in filenames)

	c_libs = tuple(sl for sl in sublibs if sl[0] in ("h", "hpp"))

	for ext, lib_name, filepath in c_libs :#XXX XXX XXX WRONG!!!!!!!!! do not test lib type this way - is there actually something like library type?! XXX XXX XXX
		blocks = load_c_module(lib_name, filepath)#XXX first gather all files
		include_files.append(filepath)
		items.extend([ (be_lib_block_t(lib_name, filepath, "c", b.type_name, b.type_name), b)
			for b in blocks ])

	w_libs = tuple(sl for sl in sublibs if sl[0] == "w")

	for ext, lib_name, filepath in w_libs :
		blocks = load_workbench_library(lib_name, [ filepath ])
#		include_files.append(f)
		items.extend([ (be_lib_block_t(lib_name, filepath, "w", b.type_name, b.type_name), b)
			for b in blocks ])

	return be_library_t(
		name=lib_base_name,
		path=path,
		allowed_targets=None,#TODO
		include_files=include_files,
		items=items)



lib_file_info_t = namedtuple("lib_file_info", ("path", "file_type", "using_types"))


lib_info_t = namedtuple("lib_info", ("lib_name", "path", "files", "using_types"))


def __get_lib_file_info(ext, lib_name, filepath) :
	"""
	return instance of lib_file_info_t if filepath is valid library file, None otherwise
	"""

	if ext in ("c", "h", "cpp", "hpp") :
		file_type = "c"
	elif ext in ("w", ) :
		file_type = "w"
	else :
		return None
#		raise Exception(here(), "unknown lib file extension '" + ext + "'")

	using_types = set()

	if file_type == "w" :
		dependencies = get_workbench_dependencies(filepath)
		using_types.update(dependencies)

	return lib_file_info_t(
		path=filepath,
		file_type=file_type,
		using_types=tuple(using_types))


def scan_library(lib_basedir, path) :
	"""
	return instance of lib_info_t with list of instances of lib_file_info_t
	"""

	(root, dirnames, filenames), = tuple(islice(os.walk(path), 1))

	lib_base_name = lib_name_from_path(lib_basedir, path)

	items = []
	include_files = []
	blocks = tuple()

	sublibs = (__lib_path_and_name(root, lib_base_name, f) for f in filenames)

	files = []
	for ext, lib_name, filepath in sublibs :
		file_info = __get_lib_file_info(ext, lib_name, filepath)
		if not file_info is None :
			files.append(file_info)

	return lib_info_t(
		lib_name=lib_base_name,
		path=path,
		files=(files),
		using_types=tuple())


def load_library(lib):
	"""
	return blocks loaded from library described by lib_info_t instance lib
	"""
	lib_blocks = []
	for file_info in sorted(lib.files) :
#		print "!!!"
#		pprint(file_info)
		if file_info.file_type == "c" :
			if __is_header(file_info.path) :
				blocks = load_c_module(lib.lib_name, file_info.path)
				lib_blocks += lib_blocks
		elif file_info.file_type == "w" :
#TODO
			pass
		else :
			raise Exception(here(), "unknown lib file type '" + file_info.file_type + "'")
	return lib_blocks


def sort_libs(libs) :
	"""
	from list of lib_info_t generate list of lib names topologicaly sorted by their dependencies
	"""

	g = {}
	s = []

	for lib in libs :
		deps = set()
		for file_info in lib.files :
			for full_type in file_info.using_types :
				lib_name, type_name = split_full_type_name(full_type)
				deps.add(lib_name)
		if deps :
			g[lib.lib_name] = deps
		else :
			s.append(lib.lib_name)

	reached = set(s)
	while g :
		removed = []
		for k, v in g.items() :
			if v.issubset(reached) :
				s.append(k)
				removed.append(k)
				reached.add(k)
		if g and not removed :
			print(here() + " probable cyclic dependency")
			return None
		for k in removed :
			g.pop(k)

	return s


def load_librariesNEW(lib_basedir) :
	basedir = os.path.abspath(lib_basedir)
	(dirname, dirnames, filenames), = tuple(islice(os.walk(basedir), 1))

	libs = []
	for d in dirnames :
		path = os.path.abspath(os.path.join(basedir, d))
		lib = scan_library(basedir, path)
		libs.append(lib)

	#TODO now do topological sorting

	loaded_libs = [ load_library(lib) for lib in libs ]

	return loaded_libs


def load_librariesOLD(lib_basedir) :
	basedir = os.path.abspath(lib_basedir)
	(dirname, dirnames, filenames), = tuple(islice(os.walk(basedir), 1))
	libs = []

	lib_info = []

	for d in dirnames :
		path = os.path.abspath(os.path.join(basedir, d))


#		print "------------------------>"
		xxx = scan_library(lib_basedir, path)
		lib_info.append(xxx)
#		load_library(xxx)
#		pprint(xxx)
#		print "<<======================="



		lib = read_lib_dir(basedir, path)
		libs.append(lib)


	sort_libs(lib_info)

	return libs


def load_libraries(lib_basedir) :
	return load_librariesOLD(lib_basedir)
#	return load_librariesNEW(lib_basedir)


# ------------------------------------------------------------------------------------------------------------


class BasicBlocksFactory(object) :


	def load_library(self, lib_basedir) :
		libs = load_libraries(lib_basedir)
		self.libs += libs
		for lib in libs :
			self.__blocks += [ proto for item, proto in lib.items ]
		return (True, )


	def get_block_by_name(self, full_type, fuzzy=True) :
		lib_name, type_name = split_full_type_name(full_type)
#		print here(), full_type, lib_name

		hits = tuple(p for p in self.__blocks
			if p.type_name == type_name and
			(True if fuzzy else (p.library == lib_name or (not p.library and not lib_name))))

		if not hits :
			raise Exception("type_name '" + full_type + "' not found")

		if not fuzzy and len(hits) > 1 :
			raise Exception("multiple hits for type_name '" + full_type + "'")

		if fuzzy :
			exact = tuple(p for p in hits if p.library == lib_name)
			return exact[0] if exact else hits[0]
		else :
			return hits[0]


	block_list = property(lambda self: self.__blocks)


	def __init__(self, scan_dir=None) :
#		print("factory init scan_dir=", scan_dir, id(self), here(10))
		self.libs = []
#TODO use (ordered) dictionary
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
			SBP("Sink", "Special", [ dfs.In(-1, "", dfs.W, .5, type_name="<infer>") ], pure=True),
			PipeProto(),
			PipeEndProto(),
			MuxProto(),

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
			SBP("divmod", "Arithmetic", [ dfs.In(-1, "n", dfs.W, .33),
				dfs.In(-2, "d", dfs.W, .66),
				dfs.Out(-1, "q", dfs.E, .33), dfs.Out(-2, "r", dfs.E, .66) ], pure=True),
			BinaryOp("lt", "Arithmetic", commutative=False),
			BinaryOp("gt", "Arithmetic", commutative=False),
			BinaryOp("eq", "Arithmetic", commutative=False),
			BinaryOp("lte", "Arithmetic", commutative=False),
			BinaryOp("gte", "Arithmetic", commutative=False),
		]
		if scan_dir :
			self.load_library(scan_dir)

# ------------------------------------------------------------------------------------------------------------

__factory_instance = None

def create_block_factory(**args) :
	global __factory_instance
	if __factory_instance is None :
		__factory_instance = BasicBlocksFactory(**args)
	return __factory_instance

# ----------------------------------------------------------------------------

def main() :
	pprint(read_lib_dir(os.path.abspath("library"), "/home/vd/personal/bloced/library/arduino"))
	sys.exit(0)

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
			exports = extract_exports(srcs, KNOWN_TYPES)
			pprint(exports)
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


if __name__ == "__main__" :
	main()


