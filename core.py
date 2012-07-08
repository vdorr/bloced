
"""
built-in blocks, types and library services
"""

import dfs
import os
import hparser
from collections import namedtuple
from itertools import count, islice
from pprint import pprint
import serializer
from utils import here
import sys
if sys.version_info.major == 3 :
	from io import StringIO
else :
	from StringIO import StringIO

# ------------------------------------------------------------------------------------------------------------

#TODO fetch type informations from some "machine support package"

type_t = namedtuple("type_t", ("size_in_words", "size_in_bytes", "priority", "arithmetic"))

TYPE_VOID = "void"
TYPE_INFERRED = "<inferred>"
VM_TYPE_CHAR = "vm_char_t"
VM_TYPE_WORD = "vm_word_t"
VM_TYPE_DWORD = "vm_dword_t"
VM_TYPE_FLOAT = "vm_float_t"
#VM_TYPE_DOUBLE = "vm_double_t" : type_t(4, 8, 4),
VM_TYPE_BOOL = "vm_bool_t"
#VM_TYPE_STRING = "vm_string_t" : None,

KNOWN_TYPES = {
	TYPE_VOID : None,
	TYPE_INFERRED : None,
	VM_TYPE_BOOL : type_t(None, None, 0, False),
	VM_TYPE_CHAR : type_t(1, 1, 0, True), #TODO
	VM_TYPE_WORD : type_t(1, 2, 1, True),
	VM_TYPE_DWORD : type_t(2, 4, 2, True),
	VM_TYPE_FLOAT : type_t(2, 4, 3, True),
}

# ------------------------------------------------------------------------------------------------------------

INPUT_TERM = 1
OUTPUT_TERM = 2

term_model_t = namedtuple("term_model_t", ("name", "default_side", "default_pos", "direction",
	"type_name", "arg_index", "variadic", "commutative", "virtual"))


def cast_issues(t0, t1) :
	"""
	test for possible issues when casting from t0 to t1
	arguments are of type type_t
	"""
	possible = False
	truncating = None
	if not None in (t0, t1) :
		possible = True #further checking will be needed with vm_string_t
		truncating = False
		if ((t0.arithmetic and not t1.arithmetic) or
				(t0.arithmetic and t1.arithmetic and t0.priority > t1.priority)) :
			truncating = True
	return possible, truncating


#def TermModel(arg_index, name, default_side, default_pos, direction, variadic, commutative,
#		type_name=None, virtual=False) :
#	return term_model_t(
#		name = name,
#		default_side = default_side,
#		default_pos = default_pos,
#		direction = direction,
#		type_name = type_name,
#		arg_index = arg_index,
#		variadic = variadic,
#		commutative = commutative,
#		virtual = virtual)


#def In(arg_index, name, default_side, default_pos,
#		type_name=core.TYPE_INFERRED,
#		variadic=False,
#		commutative=False) :
#	return TermModel(arg_index, name, default_side, default_pos, INPUT_TERM, variadic, commutative,
#			type_name=type_name)


#def Out(arg_index, name, default_side, default_pos,
#		type_name=core.TYPE_INFERRED,
#		variadic=False,
#		commutative=False) :
#	return TermModel(arg_index, name, default_side, default_pos, OUTPUT_TERM, variadic, commutative,
#			type_name=type_name)


#def VirtualIn(name) :
#	return TermModel(None, name, None, None, INPUT_TERM, False, False, virtual=True)


#def VirtualOut(name) :
#	return TermModel(None, name, None, None, OUTPUT_TERM, False, False, virtual=True)


class TermModel(object) :

	name = property(lambda self: self.__name)

	default_side = property(lambda self: self.__side)

	default_pos = property(lambda self: self.__pos)

	direction = property(lambda self: self.__direction)

	type_name = property(lambda self: self.__type_name)

	variadic = property(lambda self: self.__variadic)

	commutative = property(lambda self: self.__commutative)

	virtual = property(lambda self: self.__virtual)


	def get_term_data(self) :
		return term_model_t(
			name = self.name,
			default_side = self.default_side,
			default_pos = self.default_pos,
			direction = self.direction,
			type_name = self.type_name,
			arg_index = self.arg_index,
			variadic = self.variadic,
			commutative = self.commutative,
			virtual = self.virtual)

	def __init__(self, arg_index, name, side, pos, direction, variadic, commutative,
			type_name=None, virtual=False) :
		self.__name = name
		self.__side = side
		self.__pos = pos
		self.__direction = direction
		self.__type_name = type_name
		self.arg_index = arg_index
		self.__variadic = variadic
		self.__commutative = commutative
		self.__virtual = virtual

	def __repr__(self) :
		return "." + self.__name
#		return hex(id(self)) + " " + {INPUT_TERM:"in",OUTPUT_TERM:"out"}[self.direction] + ":" + self.name

	def __lt__(self, b) :
		return id(self) < id(b)


def term_model_from_term_data(td) :
	return TermModel(td.arg_index, td.name, td.default_side, td.default_pos, td.direction, td.variadic,
		td.commutative, type_name=td.type_name, virtual=td.virtual)


class In(TermModel) :
	def __init__(self, arg_index, name, side, pos,
			type_name=TYPE_INFERRED,
			variadic=False,
			commutative=False) :
		TermModel.__init__(self, arg_index, name, side, pos, INPUT_TERM, variadic, commutative,
			type_name=type_name)


class Out(TermModel) :
	def __init__(self, arg_index, name, side, pos,
			type_name=TYPE_INFERRED,
			variadic=False,
			commutative=False) :
		TermModel.__init__(self, arg_index, name, side, pos, OUTPUT_TERM, variadic, commutative,
			type_name=type_name)


class VirtualIn(TermModel) :
	def __init__(self, name) :
		TermModel.__init__(self, None, name, None, None, INPUT_TERM, False, False,
			virtual=True)


class VirtualOut(TermModel) :
	def __init__(self, name) :
		TermModel.__init__(self, None, name, None, None, OUTPUT_TERM, False, False,
			virtual=True)


block_proto_t = namedtuple("block_proto_t", ("type_name", "terms", "default_size",
	"exe_name", "commutative", "pure", "values", "library", "data"))


def block_proto_from_proto_data(bp) :
	args = dict(bp.__dict__)
	args.pop("type_name")
	args.pop("terms")
	return BlockPrototype(bp.type_name,
		tuple(term_model_from_term_data(t) for t in bp.terms), **args)


class BlockPrototype(object) :

	# to be shown in bloced
	type_name = property(lambda self: self.__type_name)

	# to be used in code to execute block
	exe_name = property(lambda self: self.__exe_name)

	terms = property(lambda self: self.__terms)

#	inputs = property(lambda self: [ t for t in self.__terms if t.direction == INPUT_TERM ] )

#	outputs = property(lambda self: [ t for t in self.__terms if t.direction == OUTPUT_TERM ] )
	
	category = property(lambda self: self.__category)
	
	default_size = property(lambda self: self.__default_size)

	commutative = property(lambda self: self.__commutative)

	pure = property(lambda self: self.__pure)

	values = property(lambda self: self.__values)

	library = property(lambda self: self.__library)

	data = property(lambda self: self.__data)


	def get_block_proto_data(self) :
		return block_proto_t(
			type_name=self.type_name,
			terms=tuple(t.get_term_data() for t in self.terms),
			default_size=self.default_size,
			exe_name=self.exe_name,
			commutative=self.commutative,
			pure=self.pure,
			values=self.values,
			library=self.library,
			data=None)


	def __init__(self, type_name, terms,
			exe_name=None,
			default_size=(64,64),
			category="all",
			commutative=False,
			pure=False,
			values=None,
			library=None,
			data=None) :
		self.__category = category
		self.__type_name = type_name
		self.__terms = terms
		self.__default_size = default_size
		self.__exe_name = exe_name
		self.__commutative = commutative
		self.__pure = pure
		self.__values = values
		self.__library = library
		self.__data = data
		assert(prototype_sanity_check(self))#TODO refac


# ------------------------------------------------------------------------------------------------------------

class JointProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Joint",
			[ Out(0, "y", dfs.C, 0, variadic=True), In(0, "x", dfs.C, 0) ],
			default_size=(8,8), category="Special")


class ConstProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Const",
			[ Out(0, "y", dfs.E, 0.5, type_name=TYPE_INFERRED) ],
			default_size=(96,28), category="Special",
			values=[("Value", None)])


class DelayProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Delay", [ In(0, "x", dfs.E, 0.5), Out(0, "y", dfs.W, 0.5) ],
			category="Special",
			values=[("Default", None)])


class DelayInProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "DelayIn", [ In(0, "x", dfs.W, 0.5) ])


class DelayOutProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "DelayOut", [ Out(0, "y", dfs.E, 0.5) ])


class InitDelayProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "InitDelay",
			[ In(0, "x", dfs.W, 0.33), In(0, "init", dfs.W, 0.66), Out(0, "y", dfs.E, 0.5) ],
			category="Special")


class InitDelayOutProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "InitDelayOut",
			[ In(0, "init", dfs.W, 0.5), Out(0, "y", dfs.E, 0.5) ])


class ProbeProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Probe", [ In(0, "x", dfs.W, 0.5) ],
			default_size=(96,28), category="Special", exe_name="probe")


class TapProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Tap", [ In(0, "x", dfs.W, 0.5) ],
			default_size=(96,28), category="Special",
			values=[("Name", None)])


class TapEndProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "TapEnd", [ Out(0, "y", dfs.E, 0.5) ],
			default_size=(96,28), category="Special",
			values=[("Name", None)])


class SignalProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Signal", [ Out(0, "y", dfs.E, 0.5) ],
			default_size=(48,48), category="Special")


class SysRqProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "SysRq",
			[ In(-1, "en", dfs.W, 0.25),
			  In(-2, "nr", dfs.W, 0.5),
			  In(-3, "x", dfs.W, 0.75, variadic=True),
			  Out(-3, "eno", dfs.E, 0.25),
			  Out(-1, "rc", dfs.E, 0.5),
			  Out(-2, "y", dfs.E, 0.75, variadic=True) ],
			exe_name="sysrq",
			default_size=(64,80), category="Special")


class InputProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Input", [ Out(0, "x", dfs.E, 0.5) ],
			default_size=(96,28), category="Special",
			values=[("Name", None)])


class OutputProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Output", [ In(0, "y", dfs.W, 0.5) ],
			default_size=(96,28), category="Special",
			values=[("Name", None)])


class PipeProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Pipe", [ In(0, "x", dfs.W, 0.5) ],
			default_size=(96,28), category="Special",
			values=[("Name", None), ("Default", None)])


class PipeEndProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "PipeEnd", [ Out(0, "y", dfs.E, 0.5) ],
			default_size=(96,28), category="Special",
			values=[("Name", None)])


class GlobalWriteProto(BlockPrototype):
	def __init__(self, type_name) :
		BlockPrototype.__init__(self, "GlobalWrite",
			[ In(0, "x", dfs.W, 0.5, type_name=type_name) ],
			default_size=(96,28),
			values=[("Name", None), ("Sync", None)])


class GlobalReadProto(BlockPrototype):
	def __init__(self, type_name) :
		BlockPrototype.__init__(self, "GlobalRead",
			[ Out(0, "y", dfs.E, 0.5, type_name=type_name) ],
			default_size=(96,28),
			values=[("Name", None), ("Sync", None)])


class FunctionCallProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "FunctionCall", [],
			values=[("Name", None)])


class MuxProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "mux", [
			In(-1, "x", dfs.W, .25, type_name=TYPE_INFERRED),#XXX should be binary
			In(-2, "a", dfs.W, .5, type_name=TYPE_INFERRED),
			In(-3, "b", dfs.W, .75, type_name=TYPE_INFERRED),
			Out(-1, "q", dfs.E, .5, type_name=TYPE_INFERRED), ],
			pure=True, category="Special")


class SBP(BlockPrototype) :
	def __init__(self, type_name, category, terms, exe_name=None, commutative=False, pure=False) :
		BlockPrototype.__init__(self, type_name, terms,
			exe_name=type_name if not exe_name else exe_name,
			category=category,
			commutative=commutative,
			pure=pure)


class UnaryOp(BlockPrototype) :
	def __init__(self, type_name, category, exe_name=None) :
		BlockPrototype.__init__(self,
			type_name,
			[ In(0, "a", dfs.W, .5), Out(0, "y", dfs.E, .5) ],
			exe_name=type_name if not exe_name else exe_name,
			category=category,
			pure=True)


class BinaryOp(BlockPrototype) :
	def __init__(self, type_name, category, exe_name=None, commutative=False,
			output_type=TYPE_INFERRED) :
		BlockPrototype.__init__(self,
			type_name,
			[ In(0, "a", dfs.W, .33), In(0, "b", dfs.W, .66),
				Out(0, "y", dfs.E, .5, type_name=output_type) ],
			exe_name=type_name if not exe_name else exe_name,
			category=category,
			commutative=commutative,
			pure=True)


class BinaryBooleanOp(BlockPrototype) :
	def __init__(self, type_name, category, exe_name=None, commutative=False) :
		BlockPrototype.__init__(self,
			type_name,
			[ In(0, "a", dfs.W, .33, type_name=VM_TYPE_BOOL),
				In(0, "b", dfs.W, .66, type_name=VM_TYPE_BOOL),
				Out(0, "y", dfs.E, .5, type_name=VM_TYPE_BOOL) ],
			exe_name=type_name if not exe_name else exe_name,
			category=category,
			commutative=commutative,
			pure=True)


class UnaryBooleanOp(BlockPrototype) :
	def __init__(self, type_name, category, exe_name=None) :
		BlockPrototype.__init__(self,
			type_name,
			[ In(0, "a", dfs.W, .5, type_name=VM_TYPE_BOOL),
				Out(0, "y", dfs.E, .5, type_name=VM_TYPE_BOOL) ],
			exe_name=type_name if not exe_name else exe_name,
			category=category,
			pure=True)


class CFunctionProto(BlockPrototype):
	pass


class MacroProto(BlockPrototype):
	pass


class FunctionProto(BlockPrototype):
	pass


class TypecastProto(BlockPrototype) :
	def __init__(self, type_name, category, to_type) :
		BlockPrototype.__init__(self,
			type_name,
			[ In(0, "a", dfs.W, .5), Out(0, "y", dfs.E, .5, type_name=to_type) ],
			exe_name=type_name,
			category=category,
			pure=True)


class TextAreaProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "TextArea", [],
			default_size=(96,28), category="Special",
			values=[("Text", "")])


# ----------------------------------------------------------------------------


def parse_vmex_line(s) :
	tokens = hparser.tokenize(s, os.linesep)
#	print "parse_vmex_line:", tokens
	if not tokens :
		return None
	ret_type, name, args_list = hparser.parse_decl(tokens)
	return ret_type, name, args_list


term_type_t = namedtuple("term", (
#	"arg_index",
	"name",
#	"side", "pos",
	"direction", "variadic", "commutative", "type_name", "index"))


def vmex_arg(a, known_types, index, variadic=False, commutative=False, direction=None) :
	sig, name = a
#	print here(), a

#	TermModel arg_index, name, side, pos, direction, variadic, commutative, type_name=None
#	name,
	if direction is None :
		direction = OUTPUT_TERM if "*" in sig else INPUT_TERM

	type_names_found = [ tp for tp in sig if tp in known_types ]
	if len(type_names_found) != 1 :
		raise Exception("unknown or ambiguous type name '{}'".format(sig))
	(type_name, ) = type_names_found
	return term_type_t(name, direction, variadic, commutative, type_name, index)


VMEX_SIG = "_VM_EXPORT_"


def is_vmex_line(s) :
	ln = s.strip()
	if not ln.startswith(VMEX_SIG) :
		return None
	return ln


def __group_vmex_args(args_list) :
	va = False
	group = []
	for sig, name in args_list :

		group.append((sig, name))

		if "_VM_VA_CNT_" in sig :
			va = True
		elif "_VM_VA_LST_" in sig :
			va = False
		else :
			va = False

		if not va :
			yield group
			group = []


#_VM_VA_CNT_ _VM_INPUT_
#_VM_VA_LST_
def parse_vmex_export(export, known_types) :
#	print here(), export
	ret_type, name, args_list = export
	assert(VMEX_SIG in ret_type)
#	print here(), name
	args_info = []

	for arg_group, i in zip(__group_vmex_args(args_list), count()) :
#		print here(), len(arg_group)

		arg_group_len = len(arg_group)
		if arg_group_len == 1 :
			a = vmex_arg(arg_group[0], known_types, i)
			args_info.append(a)
		elif arg_group_len == 2 :
			(cnt_sig, cnt_name), (lst_sig, lst_name) = arg_group
#			print here(), cnt_name, cnt_sig, lst_name, lst_sig
			if "_VM_VA_CNT_" and cnt_sig and "_VM_VA_LST_" in lst_sig and "*" in lst_sig :
				if "_VM_INPUT_" in cnt_sig :
					direction = INPUT_TERM
				elif "_VM_OUTPUT_" in cnt_sig :
					direction = OUTPUT_TERM
				else :
					raise Exception(here() + " variadic term declaration lacks direction")
				a = vmex_arg((lst_sig, lst_name), known_types, i, 
					variadic=True,
					direction=direction)
				args_info.append(a)
			else :
				raise Exception(here() + " invalid variadic term declaration")
		else :
			raise Exception(here() + " argument grouping error")

#		for sig, arg_name in arg_group :
#			print here(), arg_name

#	return name, term_type, direction, variadic, commutative

#	print here()
#	pprint(args_info)

	vmex_ret_type = None
	for tp in ret_type :
		if tp in known_types :
			vmex_ret_type = tp

	terms_in = [ a for a in args_info if a.direction == INPUT_TERM ]
	terms_out = [ a for a in args_info if a.direction == OUTPUT_TERM ]

	if not terms_out and not "void" in ret_type :
		terms_out = [ vmex_arg((ret_type, "out"), known_types, len(terms_in)) ]

#	print here(), [ai.name for ai in terms_in], [ai.name for ai in terms_out]

	return name, (terms_in, terms_out)


def extract_exports(src_str, known_types) :

	exports = []
	for tk_list in hparser.extract_declarations(hparser.tokenize2(src_str, os.linesep)) :
		preprocessed = tuple(hparser.drop_comments(tk_list))
		decl = hparser.stripped_token_list(preprocessed)
#		print here(), decl
		if VMEX_SIG in decl : #TODO deeper syntax check
			ret_type, name, args_list = hparser.parse_decl(decl)
#			print here(), "'%s'" % name, ret_type
			exports.append((ret_type, name, args_list))

	vmex_funcs = [ parse_vmex_export(vmex, known_types) for vmex in exports ]

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

	#arg_index, name, side, pos, type_name=None, variadic=False, commutative=False
	inputs = [ (arg_index, In(-i, name, dfs.W, pos,
			type_name=type_name, variadic=variadic, commutative=commutative))
		for (name, direction, variadic, commutative, type_name, arg_index), pos, i
			in zip(terms_in, in_terms_pos, count()) ]
	outputs = [ (arg_index, Out(-i, name, dfs.E, pos,
			type_name=type_name, variadic=variadic, commutative=commutative))
		for (name, direction, variadic, commutative, type_name, arg_index), pos, i
			in zip(terms_out, out_terms_pos, count()) ]

#	print here(), [ t for _, t in sorted(inputs + outputs, key=lambda itm: itm[0]) ]

	proto = CFunctionProto(block_name,
			[ t for _, t in sorted(inputs + outputs, key=lambda itm: itm[0]) ],
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


def load_c_library(lib_name, file_path) :
	exports = extract_vmex(file_path, KNOWN_TYPES)
	protos = [ __cmod_create_proto(lib_name, export) for export in exports ]
	return protos


# ------------------------------------------------------------------------------------------------------------


def guess_block_size(terms_N, terms_S, terms_W, terms_E) :
	mc_width = max([ len(terms_N) + 2, len(terms_S) + 2 ]) * dfs.TERM_SIZE
	mc_width = mc_width if mc_width >= dfs.MIN_BLOCK_WIDTH else dfs.MIN_BLOCK_WIDTH
	mc_height = max([ len(terms_W) + 2, len(terms_E) + 2 ]) * dfs.TERM_SIZE
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
	side = tb.get_term_side(tb.terms[0])
	vertical = side in (dfs.N, dfs.S)
#	print tb, x, y,  y>(k * x), y>((-k * (x-w))+u)
	return sides[vertical, y > center_y if vertical else x > center_x ]


def __mc_assign_positions(term_sides, side) :
	assert(side in (dfs.N, dfs.S, dfs.W, dfs.E))
	terms = [ (tb, sd, y if side in (dfs.N, dfs.S) else x)
		for tb, sd, (x, y) in term_sides if sd == side ]
	terms.sort(key=lambda tb_sd_y: -tb_sd_y[2])#(tb, sd, y): y)
	step = 1.0 / (len(terms) + 1)
	term_positions = [ (tb, sd, (i + 1) * step) for (tb, sd, p), i in zip(terms, count()) ]
#	print here(), "step=", step, "term_positions=", term_positions
	return term_positions


def try_mkmac(model) :
#	inputs = [ b for b in model.blocks if isinstance(b.prototype, InputProto) ]
#	outputs = [ b for b in model.blocks if isinstance(b.prototype, OutputProto) ]

	terms = [ __mc_term_info(model, b)
		for b in model.blocks if b.prototype.__class__ in (InputProto, OutputProto) ]
#	print("try_mkmac:", terms)

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
#	print("try_mkmac: l, t, r, b, w,h=", l, t, r, b, r-l, b-t)

	term_sides = [ (tb, __mc_assign_side(tb, l+((r-l)/2), t+((b-t)/2), x, y), (x, y)) for tb, (x, y) in terms]
#	xxx = [ (tb, __mc_assign_side(tb, k, (r-l)/2, (b-t), x, y)) for tb, (x, y) in terms]
#	print("try_mkmac: sides=", term_sides)

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

#	print("term_positions=", mc_width, mc_height, term_positions)

	return mc_width, mc_height, term_positions
#	graph, delays = make_dag(model, {})
#	pprint(graph)


def is_builtin_block(prototype) :
	"""
	return True if prototype instance is for built in block
	"""
	return not bool(prototype.library)


def is_macro_name(s) :
	return s.strip().startswith("@macro:")


def get_macro_name(s) :
	if not is_macro_name(s) :
		return None
	return s.split(":")[-1]


def is_function_name(s) :
	return s.strip().startswith("@function:")


def get_function_name(s) :
	if not is_function_name(s) :
		return None
	return s.split(":")[-1]


def sheet_block_name(s) :
	name, _ = sheet_block_name_and_class(s)
	return name


def sheet_block_name_and_class(s) :
	parts = s.split(":")
	if len(parts) != 2 :
		return None
	prefix, name = parts
	if prefix == "@macro" : #TODO name sheet prefixs
		return name, MacroProto
	elif prefix == "@function" :
		return name, FunctionProto
	else :
		return None


lib_block_data_t = namedtuple("lib_block_data", ("raw_workbench", "raw_sheet", "cooked_workbench", "cooked_sheet"))


def create_proto_from_sheet(sheet_name, sheet) :
	block_name, proto_class = sheet_block_name_and_class(sheet_name)
	return __create_sheet_wrapper("<local>", block_name, sheet, proto_class)


def __create_sheet_wrapper(lib_name, block_name, sheet, prototype_type) :

	width, height, terms = try_mkmac(sheet)

#	for t, side, pos in terms :
#		term_name, = t.value

#		variadic = False #TODO infer from connected block
#		commutative = False #TODO infer from connected block
#		type_name = TYPE_INFERRED #TODO infer from connected block

#		print(here(), term_name, side, pos)

	terms_in = [ (t.value[0], INPUT_TERM, False, False, TYPE_INFERRED, pos, side)
		for t, side, pos in terms if t.prototype.__class__ == InputProto ]
	terms_out = [ (t.value[0], OUTPUT_TERM, False, False, TYPE_INFERRED, pos, side)
		for t, side, pos in terms if t.prototype.__class__ == OutputProto ]

	inputs = [ In(-i, name, side, pos,
			type_name=type_name, variadic=variadic, commutative=commutative)
		for (name, direction, variadic, commutative, type_name, pos, side), i
			in zip(terms_in, count()) ]
	outputs = [ Out(-i, name, side, pos,
			type_name=type_name, variadic=variadic, commutative=commutative)
		for (name, direction, variadic, commutative, type_name, pos, side), i
			in zip(terms_out, count()) ]

	proto = prototype_type(block_name,
			inputs + outputs,
			exe_name=block_name,
			default_size=(width, height),
			category=lib_name,
			library=lib_name,
			data=lib_block_data_t(None, None, None, sheet))

	return proto


def __create_macro(lib_name, block_name, sheet) :
	return __create_sheet_wrapper(lib_name, block_name, sheet, MacroProto)


def __create_function(lib_name, block_name, sheet) :
	return __create_sheet_wrapper(lib_name, block_name, sheet, FunctionProto)


def load_workbench_library(lib_name, file_path, library=None, w_data=None) :
	"""
	lib_name - full library name, example 'logic.flipflops'
	"""
	if file_path is None :
		data = w_data
	else :
		with open(file_path, "rb") as f :
			data = serializer.unpickle_workbench_data(f)
	w = dfs.Workbench(
#		lib_dir=os.path.join(os.getcwd(), "library"),
		blockfactory=library,
		passive=True,
		do_create_block_factory=False)
	serializer.restore_workbench(data, w, library=library)
	return load_blocks_from_workbench(w, lib_name)


def load_blocks_from_workbench(w, lib_name) :
	"""
	load macroes and functions from dfs.Workbench w
	"""
	blocks = []
	for (name, sheet) in w.sheets.items() :
		if is_macro_name(name) :
			block_name = get_macro_name(name)
			proto = __create_macro(lib_name, block_name, sheet)
			blocks.append(proto)
		elif is_function_name(name) :
			block_name = get_function_name(name)
			proto = __create_function(lib_name, block_name, sheet)
			blocks.append(proto)
	return blocks


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
				lib_name, type_name = split_full_type_name(block_type)
				if lib_name :
					used_types.update((block_type,))

	return used_types


#-------------------------------------------------------------------------------------------------------------


be_lib_block_t = namedtuple("be_lib_item",  ("library", "file_path", "src_type", "name", "block_name"))


be_library_t = namedtuple("be_library", ("name", "path", "allowed_targets", "include_files", "source_files", "items"))


def split_full_type_name(full_type) :
	type_name_parts = full_type.split(".")
	type_name = type_name_parts[-1]
	lib_name = ".".join(type_name_parts[:-1])
	return lib_name, type_name


#def read_be_lib_file(path) :
#	pass


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


def load_standalone_workbench_lib(path, lib_base_name, library=None, w_data=None) :
	"""
	return blocks loaded from .w library pointed to by path
	"""

#	root = os.path.dirname(path)
#	lib_base_name = lib_name_from_path(root, path)

#	ext, lib_name, _ = __lib_path_and_name(root, lib_base_name, path)
#	file_info = __get_lib_file_info(ext, lib_name, path)
#	if file_info is None :
#		return None #XXX Exception?
	file_info = lib_file_info_t(
		path=path,
		file_type="w",
		using_types=tuple())

	lib = lib_info_t(
		lib_name=lib_base_name,
		path=path,
		files=(file_info,),
		using_types=tuple())

	lib_items = []
	for file_info in sorted(lib.files) :

		blocks = load_workbench_library(lib.lib_name, file_info.path, library=library, w_data=w_data)

		items = [ (be_lib_block_t(lib.lib_name, file_info.path, file_info.file_type, b.type_name, b.type_name), b)
			for b in blocks ]
		lib_items.extend(items)

	return be_library_t(
		name=lib.lib_name,
		path=lib.path,
		allowed_targets=None,#TODO
		include_files=None,
		source_files=(path,),
		items=lib_items)


def scan_library(lib_basedir, path) :
	"""
	return instance of lib_info_t with list of instances of lib_file_info_t
	"""

	(root, _, filenames), = tuple(islice(os.walk(path), 1))

	lib_base_name = lib_name_from_path(lib_basedir, path)

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


def load_library(lib, library=None) :
	"""
	return blocks loaded from library described by lib_info_t instance lib
	"""
	lib_items = []
	include_files = []
	source_files = []
	for file_info in sorted(lib.files) :

		blocks = []

		if file_info.file_type == "c" :
			if __is_header(file_info.path) :
				include_files.append(file_info.path)
				blocks = load_c_library(lib.lib_name, file_info.path)
			else :
				source_files.append(file_info.path)#XXX is this filter sufficient
#				print here(), file_info.path
		elif file_info.file_type == "w" :
			blocks = load_workbench_library(lib.lib_name, file_info.path, library=library)
		else :
			raise Exception(here(), "unknown lib file type '" + file_info.file_type + "'")

		items = [ (be_lib_block_t(lib.lib_name, file_info.path, file_info.file_type, b.type_name, b.type_name), b)
			for b in blocks ]
		lib_items.extend(items)

	return be_library_t(
		name=lib.lib_name,
		path=lib.path,
		allowed_targets=None,#TODO
		include_files=tuple(include_files),#f.path for f in lib.files),
		source_files=tuple(source_files),
		items=lib_items)


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


def load_library_sheet(library, full_name, sheet_name, w_data=None) :
	"""
	search library for item full_name and return sheet with sheet_name from this context
	raises Exception if there is problem, returns None if just not found
	"""
	lib_data = library.get_block_and_lib(full_name)

	if lib_data is None :
		raise Exception("library item '" + full_name + "' not found")

	lib, (item, proto) = lib_data

	if w_data is None :
		with open(item.file_path) as f :
			w_data = serializer.unpickle_workbench_data(f)

	res_found = tuple(serializer.get_resource(w_data, serializer.RES_TYPE_SHEET, None, sheet_name))

	if res_found is None :
		raise Exception("can not load library item '" + full_name + "'")

	sheet_data, = res_found
	sheet = serializer.restore_dfs_model(*(sheet_data + (library,)))

	return sheet


#TODO refac needed
def compare_proto_to_type(prototype_instance, *prototype_types) :
#	print here(), prototype_instance, prototype_instance.__class__, prototype_types, prototype_instance.__class__ in prototype_types
	return prototype_instance.__class__ in prototype_types


#TODO refac needed
def get_proto_name(prototype) :
	return prototype.__class__.__name__


def get_block_sheets(w) :
	"""
	return macro/function sheet names from workbench instance w
	"""
	return tuple(name for name in w.sheets if is_macro_name(name) or is_function_name(name))


def prototype_sanity_check(proto) :
	"""
	return (True, None) if prototype instance proto makes sense and (False, reason) if not
	"""
	errors = []
#term direction
	weird_term_dir = tuple(t for t in proto.terms if not t.direction in (INPUT_TERM, OUTPUT_TERM))
	if weird_term_dir :
		errors.append(("unknown_term_direction", weird_term_dir))
#term name uniqness
	unique_terms = set()
	colliding_terms = set()
	for t in proto.terms :
		if t.name in unique_terms :
			colliding_terms.add(t.name)
		unique_terms.add(t.name)
	if colliding_terms :
		errors.append(("colliding_term_names", colliding_terms))
#term types are in KNOWN_TYPES
	unknown_term_type = tuple(t for t in proto.terms if not t.type_name in KNOWN_TYPES)
	if unknown_term_type :
		errors.append(("unknown_term_type", unknown_term_type))
#has category or library
	if proto.category and not proto.library :
		errors.append(("no_cat_nor_lib", None))

	return (False, tuple(errors)) if errors else (True, None)


def clone_sheet(sheet, lib) :
	f = StringIO()
	serializer.pickle_dfs_model(sheet, f)
	f.seek(0)
	cloned = serializer.unpickle_dfs_model(f, lib=lib, use_cached_proto=False)
	return cloned


# ------------------------------------------------------------------------------------------------------------

def builtin_blocks() :
#TODO use (ordered) dictionary
	return [
		JointProto(),
		ConstProto(),
		DelayProto(),

		InitDelayProto(),

		ProbeProto(),
		TapProto(),
		TapEndProto(),
#		SignalProto(),
#		NoteProto(),
		SysRqProto(),
		InputProto(),
		OutputProto(),
		SBP("Sink", "Special", [ In(-1, "", dfs.W, .5, type_name="<infer>") ], pure=True),
		PipeProto(),
		PipeEndProto(),
		MuxProto(),
		TextAreaProto(),

		BinaryBooleanOp("xor", "Logic", commutative=True),
		BinaryBooleanOp("or", "Logic", commutative=True),
		BinaryBooleanOp("nor", "Logic", commutative=True),
		BinaryBooleanOp("and", "Logic", commutative=True),
		BinaryBooleanOp("nand", "Logic", commutative=True),
		UnaryBooleanOp("not", "Logic"),

		BinaryOp("bwxor", "Bitwise Logic", commutative=True),
		BinaryOp("bwor", "Bitwise Logic", commutative=True),
		BinaryOp("bwnor", "Bitwise Logic", commutative=True),
		BinaryOp("bwand", "Bitwise Logic", commutative=True),
		BinaryOp("bwnand", "Bitwise Logic", commutative=True),
		UnaryOp("bwnot", "Bitwise Logic"),
		BinaryOp("lsl", "Bitwise Logic", commutative=False),
		BinaryOp("lsr", "Bitwise Logic", commutative=False),

		BinaryOp("add", "Arithmetic", commutative=True),
		BinaryOp("sub", "Arithmetic", commutative=False),
		BinaryOp("mul", "Arithmetic", commutative=True),
		BinaryOp("div", "Arithmetic", commutative=False),
		BinaryOp("mod", "Arithmetic", commutative=False),
#		SBP("divmod", "Arithmetic", [ In(-1, "n", dfs.W, .33),
#			In(-2, "d", dfs.W, .66),
#			Out(-1, "q", dfs.E, .33), Out(-2, "r", dfs.E, .66) ], pure=True),
		UnaryOp("abs", "Arithmetic"),
		BinaryOp("lt", "Arithmetic", commutative=False, output_type=VM_TYPE_BOOL),
		BinaryOp("gt", "Arithmetic", commutative=False, output_type=VM_TYPE_BOOL),
		BinaryOp("eq", "Arithmetic", commutative=False, output_type=VM_TYPE_BOOL),
		BinaryOp("lte", "Arithmetic", commutative=False, output_type=VM_TYPE_BOOL),
		BinaryOp("gte", "Arithmetic", commutative=False, output_type=VM_TYPE_BOOL),

		TypecastProto("bool", "Type Casting", VM_TYPE_BOOL),
		TypecastProto("char", "Type Casting", VM_TYPE_CHAR),
		TypecastProto("word", "Type Casting", VM_TYPE_WORD),
		TypecastProto("dword", "Type Casting", VM_TYPE_DWORD),
		TypecastProto("float", "Type Casting", VM_TYPE_FLOAT),
	]


class BasicBlocksFactory(object) :


	def load_library(self, lib_basedir) :

		basedir = os.path.abspath(lib_basedir)
		dir_walk = tuple(islice(os.walk(basedir), 1))
		if not dir_walk :
			return None
		(_, dirnames, _), = dir_walk

		libs = {}
		for d in dirnames :
			path = os.path.abspath(os.path.join(basedir, d))
			lib = scan_library(basedir, path)
			libs[lib.lib_name] = lib

		sorted_libs = sort_libs(libs.values())

		for l in sorted_libs :
			loaded = load_library(libs[l])
			self.libs.append(loaded)
			for item, proto in loaded.items :
				ok, errors = prototype_sanity_check(proto)
				if ok :
					self.__blocks.append(proto)
				else :
					print(here(), "skipped proto", proto, "because", errors)
		return (True, )


	def load_standalone_workbench_lib(self, path, lib_name, library=None, w_data=None) :
		loaded = load_standalone_workbench_lib(path, lib_name, library=library, w_data=w_data)
		self.libs.append(loaded)
		for item, proto in loaded.items :
			ok, errors = prototype_sanity_check(proto)
			if ok :
				self.__blocks.append(proto)
			else :
				print(here(), "skipped proto", proto, "because", errors)

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


	def get_block_and_lib(self, full_type) :
		lib_name, type_name = split_full_type_name(full_type)
		libs_found = [ l for l in self.libs if l.name == lib_name ]
		if not len(libs_found) :
			return None
		lib = libs_found[0]
		blocks_found = [ (item, proto) for item, proto in lib.items if item.name == type_name ]
		if not len(blocks_found) :
			return None
		return lib, blocks_found[0]


	block_list = property(lambda self: self.__blocks)


	def get_lib_files(self) :
		return (l for llst in self.libs for l in llst.source_files)
#		return (l for l in self.libs)


	def __init__(self, load_basic_blocks=True) :
#		print("factory init scan_dir=", scan_dir, id(self), here(10))
		self.libs = []
		self.__blocks = []
		if load_basic_blocks :
			self.__blocks += builtin_blocks()


class SuperLibrary(object) :
	"""
	copies interface of BasicBlocksFactory (except for block_list), merging multiple libraries
	intended for handling local blocks and multiple library paths while keeping them separated
	"""

	def get_block_by_name(self, full_type, fuzzy=True) :
		for l in self.librarians :
			try :
				hit = l.get_block_by_name(full_type, fuzzy=fuzzy)
			except Exception :
				pass
			else :
				return hit
		raise Exception("type_name '" + full_type + "' not found")


	def get_block_and_lib(self, full_type) :
		for l in self.librarians :
			hit = l.get_block_and_lib(full_type)
			if not hit is None :
				return hit


	def load_library(self, lib_basedir) :
		l = BasicBlocksFactory(load_basic_blocks=False)
		self.librarians.append(l)
		return l.load_library(lib_basedir)


	def get_libs(self) :
		for l in self.librarians :
			for lib in l.libs :
				yield lib


	libs = property(lambda self: self.get_libs())


	def __init__(self, librarians) :
		"""
		librarians is list of BasicBlocksFactory instances
		"""
		self.librarians = librarians


# ------------------------------------------------------------------------------------------------------------

__factory_instance = None

def create_block_factory(scan_dir=None) :
	"""
	returns instance of block factory with built-in blocks and blocks loaded from scan_dir
	scan_dir is processed only at first call
	"""
	global __factory_instance
	if __factory_instance is None :
		__factory_instance = BasicBlocksFactory()
		if scan_dir :
			__factory_instance.load_library(scan_dir)
	return __factory_instance

# ------------------------------------------------------------------------------------------------------------

