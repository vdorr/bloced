
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
		BlockPrototype.__init__(self, "Const", [ Out("y", E, 0.5) ],
			default_size=(96,28), category="Special")

class DelayProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Delay", [ In("x", E, 0.5), Out("y", W, 0.5) ],
			category="Special")
		self.loop_break = True

class ProbeProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Probe", [ In("x", W, 0.5) ],
			default_size=(28,28), category="Special")

class GotoProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Goto", [ Out("x", E, 0.5) ],
			default_size=(96,28), category="Special")

class LabelProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Label", [ In("y", W, 0.5) ],
			default_size=(96,28), category="Special")

class NoteProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Note", [ ],
			default_size=(96,28), category="Special")

class DelayInProto(BlockPrototype):

#	def __repr__(self) :
#		return "%s(%i)"%(self.__name, self.nr)

	def __init__(self) :
		BlockPrototype.__init__(self, "DelayIn", [ In("x", W, 0.5) ])
#		self.nr = -1

class DelayOutProto(BlockPrototype):

#	def __repr__(self) :
#		return "%s(%i)"%(self.__name, self.nr)

	def __init__(self) :
		BlockPrototype.__init__(self, "DelayOut", [ Out("y", E, 0.5) ])
#		self.nr = -1

class SignalProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "Signal", [ Out("y", E, 0.5) ],
			default_size=(48,48), category="Special")

class SysRqProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "SysRq",
			[ In("en", W, 0.25),
			  In("nr", W, 0.5),
			  In("x", W, 0.75, variadic=True),
			  Out("eno", E, 0.25),
			  Out("rc", E, 0.5),
			  Out("y", E, 0.75, variadic=True) ],
			exe_name="sysrq",
			default_size=(64,80), category="Special")

# ------------------------------------------------------------------------------------------------------------

class SBP(BlockPrototype) :
	def __init__(self, type_name, category, terms, exe_name=None) :
		BlockPrototype.__init__(self, type_name, terms,
			exe_name=type_name if not exe_name else exe_name,
			category=category)

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
			GotoProto(),
			LabelProto(),
			SignalProto(),
			NoteProto(),
			SysRqProto(),

			SBP("xor", "Logic", [ In("a", W, .33), In("b", W, .66), Out("y", E, .5) ]),
			SBP("or", "Logic", [ In("a", W, .33), In("b", W, .66), Out("y", E, .5) ]),
			SBP("nor", "Logic", [ In("a", W, .33), In("b", W, .66), Out("y", E, .5) ]),
			SBP("and", "Logic", [ In("a", W, .33), In("b", W, .66), Out("y", E, .5) ]),
			SBP("nand", "Logic", [ In("a", W, .33), In("b", W, .66), Out("y", E, .5) ]),
			SBP("not", "Logic", [ In("a", W, .5), Out("y", E, .5) ]),

			SBP("add", "Arithmetic", [ In("a", W, .33), In("b", W, .66), Out("y", E, .5) ]),
			SBP("sub", "Arithmetic", [ In("a", W, .33), In("b", W, .66), Out("y", E, .5) ]),
			SBP("mul", "Arithmetic", [ In("a", W, .33), In("b", W, .66), Out("y", E, .5) ]),
			SBP("div", "Arithmetic", [ In("n", W, .33), In("d", W, .66), Out("y", E, .5) ]),
			SBP("mod", "Arithmetic", [ In("n", W, .33), In("d", W, .66), Out("y", E, .5) ]),
			SBP("divmod", "Arithmetic", [ In("n", W, .33), In("d", W, .66),
				Out("q", E, .33), Out("r", E, .66)  ]),

			SBP("load", "Memory", [ ]),
			SBP("store", "Memory", [ ]),
			SBP("load_nv", "Memory", [ ]),
			SBP("store_nv", "Memory", [ ]),

			SBP("di", "Process IO", [ In("nr", W, .5), Out("y", E, .5) ], exe_name="io_di"),
			SBP("do", "Process IO", [ In("nr", W, .33), In("x", W, .66) ], exe_name="io_do"),
		]

# ------------------------------------------------------------------------------------------------------------

def create_block_factory() :
	return BasicBlocksFactory()

# ------------------------------------------------------------------------------------------------------------

