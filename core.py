
from dfs import *

# ------------------------------------------------------------------------------------------------------------

class BlockFactory(object) :

	block_list = property(lambda self: self.__blocks)

	def __init__(self) :
		self.__blocks = []

# ------------------------------------------------------------------------------------------------------------

class JointProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Joint", [], default_size=(8,8), category="Special")

class ConstProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Const", [ Out(0, "y", E, 0.5) ],
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

class GotoProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Goto", [ Out(0, "x", E, 0.5) ],
			default_size=(96,28), category="Special")

class LabelProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Label", [ In(0, "y", W, 0.5) ],
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

# ------------------------------------------------------------------------------------------------------------

#TODO

def __load_macro(fname) :
	return (fname, proto, graph_snippet)

#TODO

# ------------------------------------------------------------------------------------------------------------

class BasicBlocksFactory(BlockFactory) :

	def get_block_by_name(self, type_name) :
		p = list(islice(dropwhile(lambda proto: proto.type_name != type_name,
			self._BlockFactory__blocks), 0, 1))
		if not p :
			raise Exception("type_name '" + type_name + "' not found")
		return p[0]#.__class__()

	def __init__(self) :
		BlockFactory.__init__(self)
		self._BlockFactory__blocks += [
			JointProto(),
			ConstProto(),
			DelayProto(),
			ProbeProto(),
#			GotoProto(),
#			LabelProto(),
#			SignalProto(),
#			NoteProto(),
			SysRqProto(),

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
				Out(-1, "q", E, .33), Out(-2, "r", E, .66)  ], pure=True),

			SBP("load", "Memory", [ ]),
			SBP("store", "Memory", [ ]),
			SBP("load_nv", "Memory", [ ]),
			SBP("store_nv", "Memory", [ ]),

			SBP("di", "Process IO", [ In(0, "nr", W, .5), Out(0, "y", E, .5) ], exe_name="io_di"),
			SBP("do", "Process IO", [ In(-1, "nr", W, .33), In(-2, "x", W, .66) ], exe_name="io_do"),
		]

# ------------------------------------------------------------------------------------------------------------

def create_block_factory() :
	return BasicBlocksFactory()

# ------------------------------------------------------------------------------------------------------------

