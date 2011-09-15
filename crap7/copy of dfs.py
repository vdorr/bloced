
#from Tkinter import N, S, W, E
from itertools import dropwhile, islice
import traceback

#TODO docstring

# ------------------------------------------------------------------------------------------------------------

#TODO replace usages of Tkinter stuff elsewhere
C = "C"
N = "n"
S = "s"
W = "w"
E = "e"

INPUT_TERM = 1
OUTPUT_TERM = 2

# ------------------------------------------------------------------------------------------------------------

class TermModel(object) :

	def get_location_on_block(self, bm) :
		xo, yo = bm.left, bm.top
		p = self.get_pos(bm)
		sides = {
			N : lambda: (int(xo + p * bm.width), yo),
			S : lambda: (int(xo + p * bm.width), yo + bm.height),
			W : lambda: (xo, int(yo + p * bm.height)),
			E : lambda: (xo + bm.width, int(yo + p * bm.height)),
			C : lambda: (xo + 0.5 * bm.width, int(yo + 0.5 * bm.height)),
		}
		return sides[self.get_side(bm)]()

	name = property(lambda self: self.__name)

	def get_side(self, bm) :
		flipv, fliph, rot = bm.orientation # bm.get_meta()["orientation"]
		ors = {
			W: 2 if fliph else 0,
			N: 3 if flipv else 1,
			E: 0 if fliph else 2,
			S: 1 if flipv else 3
		}
		if self.__side != C :
			old_or = ors[self.__side]
			side = [ W, N, E, S ][ (ors[self.__side] + rot / 90) % 4 ]
			return side
		return self.__side

#	side = property(__get_side)
	
	def get_pos(self, bm) :
		x, y, z = bm.orientation
		return (1 - self.__pos) if x or y else self.__pos
#		if x :
#			return (2 * (orgy - tt)) + tt
#		elif y:
#			return (2 * (orgx - ll)) + ll
		

#	pos = property(lambda self: self.__pos)

	direction = property(lambda self: self.__direction)

	type_name = property(lambda self: self.__type_name)

	def __init__(self, name, side, pos, direction, type_name=None) :
		self.__name, self.__side, self.__pos, self.__direction, self.__type_name = (
			name, side, pos, direction, type_name )

	def __repr__(self) :
		return hex(id(self)) + " " + {INPUT_TERM:"in",OUTPUT_TERM:"out"}[self.direction] + ":" + self.name

class In(TermModel) :
	def __init__(self, name, side, pos, type_name=None) :
		TermModel.__init__(self, name, side, pos, INPUT_TERM)

class Out(TermModel) :
	def __init__(self, name, side, pos, type_name=None) :
		TermModel.__init__(self, name, side, pos, OUTPUT_TERM)

# ------------------------------------------------------------------------------------------------------------

class BlockModel(object) :

	def __raise_block_changed(self, e) :
		self.__model._GraphModel__on_block_changed(self, event=e)
#		for listener in self.__model.listeners :
#			listener.block_changed(self, event=e);

	def __set_value(self, value) :
		self.__value = value
#		if self.value :
#			self.caption = self.prototype.get_type_name() + " (" + str(self.value) + ")"
		self.__raise_block_changed({"p":"value"})

	int_left = property(lambda self: self.__left)

	int_top = property(lambda self: self.__top)

	value = property(lambda self: self.__value, __set_value)

	def __set_caption(self, v) :
		self.__set_caption = v
		self.__raise_block_changed({"p":"caption"})

	caption = property(lambda self: self.__caption, __set_caption)

	def get_meta(self) :
		return {
			"caption" : self.caption,
			"left" : self.left,
			"top" : self.top,
			"width" : self.width,
			"height" : self.height,
			"value" : self.value,
			"orientation" : self.orientation,
		}

	def set_meta(self, meta) :
		for k, v in meta.iteritems() :
			self.__getattribute__("_BlockModel__set_"+k)(v)
			self.__raise_block_changed({"p":k})

	terms = property(lambda self: self.__terms)#XXX return copy instead of my instance?

	def __get_orientation(self) :
		return self.__orientation

	def __set_orientation(self, v) :
		self.__orientation = v
		self.__raise_block_changed({"p":"orientation"})

	orientation = property(__get_orientation, __set_orientation)

	def __get_width(self) :
		return self.__height if self.orientation[2] % 180 else self.__width

	def __set_width(self, v) :
		if self.orientation[2] % 180 :
			self.__height = v
		else :
			self.__width = v
		self.__raise_block_changed({"p":"width"})

	width = property(__get_width, __set_width)

	def __get_height(self) :
		return self.__width if self.orientation[2] % 180 else self.__height

	def __set_height(self, v) :
		if self.orientation[2] % 180 :
			self.__width = v
		else :
			self.__height = v
		self.__raise_block_changed({"p":"height"})

	height = property(__get_height, __set_height)

	def __get_left(self) :
		return self.__left + ((self.__width - self.__height) / 2 if self.orientation[2] % 180 else 0)

	def __set_left(self, v) :
		self.__left = v - ((self.__width - self.__height) / 2 if self.orientation[2] % 180 else 0)
		self.__raise_block_changed({"p":"left"})

	left = property(__get_left, __set_left)

	def __get_top(self) :
		return self.__top + ((self.__height - self.__width) / 2 if self.orientation[2] % 180 else 0)

	def __set_top(self, v) :
		self.__top = v - ((self.__height - self.__width) / 2 if self.orientation[2] % 180 else 0)
		self.__raise_block_changed({"p":"top"})

	top = property(__get_top, __set_top)

	prototype = property(lambda self: self.__prototype)

	def __get_center(self) :
		return self.left+(self.width/2), self.top+(self.height/2)

	def __set_center(self, v) :
		self.left = v[0] - (self.width/2)
		self.top = v[1] - (self.height/2)

	center = property(__get_center, __set_center)
	
#	def __get__connections(self) :
##		print self.__graph.connections
#		return None#self.__graph.connections.iteritems()

#	connections = property(__get__connections)

	def __my_init(self, model, caption, left, top, width, height, terms) :
		self.__orientation = (0, 0, 0)
		self.__caption, self.__left, self.__top, self.__width, self.__height, self.__terms = (
			caption, left, top, width, height, terms)
		self.__model = model
		self.__can_move = True
		self.__prototype = None
		self.__value = None

	def __init__(self, prototype, model, left = 0, top = 0) :
		self.__my_init(model, prototype.type_name, left, top,
			prototype.default_size[0], prototype.default_size[1],
			prototype.terms)
		self.__prototype = prototype

	def __repr__(self) :
		#return "block proto=" + type(self.prototype).__name__
		#return 'block"' + self.prototype.type_name + '"'
		return hex(id(self)) + " " + 'blck"' + self.__caption + '"'# + str(id(self))

# ------------------------------------------------------------------------------------------------------------

class GraphModelListener(object) :
	def block_added(self, block) : pass
	def block_removed(self, block) : pass
	def block_changed(self, block, event=None) : pass
	def connection_added(self, sb, st, tb, tt, deserializing=False) : pass
	def connection_removed(self, sb, st, tb, tt) : pass
	def connection_changed(self, sb, st, tb, tt) : pass #TODO monitoring etc.

# ------------------------------------------------------------------------------------------------------------

class GraphModel(object) :

#	def get_meta(self) :
#		return {} # TODO implement it and make it property

#	def set_meta(self) :
#		self.__assert_editing()
#		pass # TODO implement it and make it property

	def add_listener(self, listener) :
		self.listeners.append(listener)

	def remove_listener(self, listener) :
		self.listeners.remove(listener)

	# ---------------------------------------------------------------------------------

	def add_block(self, block) :
		self.blocks.append(block)
#		block.graph = self #XXX ?
		self.__history_frame_append("block_added", (block, ))
		self.__on_block_added(block)

	def remove_block(self, block) :
		self.blocks.remove(block)
		
		succs = [ c for c in self.connections.iteritems() if c[0][0] == block ]
#		succs = filter(lambda c: c[0][0] == block, self.connections.iteritems())

		for s, dests in succs :
			for d in dests :
				self.remove_connection(*(s+d))

#		preds = filter(lambda c: reduce(lambda a, dest: a or dest[0] == block, c[1], False),
#			self.connections.iteritems())
		preds = [ c for c in self.connections.iteritems()
			if reduce(lambda a, dest: a or dest[0] == block, c[1], False) ]
		for s, dests in preds :
#			for d in filter(lambda dest: dest[0] == block, dests) :
			for d in [ dest for dest in dests if dest[0] == block ] :
				self.remove_connection(*(s+d))
		
#		block.graph = None #XXX ?!

		self.__history_frame_append("block_removed", (block, ))
		self.__on_block_removed(block)

	def can_connect(self, sb, st, tb, tt) :
		return (st.direction != tt.direction and st.direction in (INPUT_TERM, OUTPUT_TERM) and
			tt.direction in (INPUT_TERM, OUTPUT_TERM))

	def set_connection_meta(self, b0, t0, b1, t1, meta) :
		old_meta = self.__connections_meta[(b0, t0, b1, t1)]
		if (b0, t0, b1, t1) in self.__connections_meta :
			self.__connections_meta[(b0, t0, b1, t1)] = meta
		else :
			self.__connections_meta[(b0, t0, b1, t1)].update(meta)

		self.__history_frame_append("connection_meta", (b0, t0, b1, t1, old_meta))
		self.__on_connection_changed(b0, t0, b1, t1)

	def get_connection_meta(self, b0, t0, b1, t1) :
		return self.__connections_meta[(b0, t0, b1, t1)]

	def add_connection(self, b0, t0, b1, t1, meta={}, deserializing=False) :
		if not self.can_connect(b0, t0, b1, t1) :
			raise Exception("can't connect")
		b0, t0, b1, t1 = (b0, t0, b1, t1) if t0.direction == OUTPUT_TERM else (b1, t1, b0, t0)

		if (b0, t0) in self.__connections :
			self.__connections[(b0, t0)].append((b1, t1))
		else :
			self.__connections[(b0, t0)] = [(b1, t1)]
		self.connections_meta[(b0, t0, b1, t1)] = meta

		self.__history_frame_append("connection_added", ((b0, t0, b1, t1), meta))
		self.__on_connection_added(b0, t0, b1, t1, deserializing=deserializing)

	def remove_connection(self, b0, t0, b1, t1) :
#		if (b0, t0) in self.__connections :
		i = self.__connections[(b0, t0)]
		i.remove((b1, t1))
		if not i :
			self.__connections.pop((b0, t0))
		meta = None
		if (b0, t0, b1, t1) in self.__connections_meta :
			meta = self.__connections_meta.pop((b0, t0, b1, t1))

		self.__history_frame_append("connection_removed", ((b0, t0, b1, t1), meta))
		self.__on_connection_removed(b0, t0, b1, t1)

	# ---------------------------------------------------------------------------------

	def __on_block_added(self, block) :
		for listener in self.__listeners :
			listener.block_added(block)

	def __on_block_removed(self, block) :
		for listener in self.__listeners :
			listener.block_removed(block)

	def __on_block_changed(self, block, event=None) :
		self.__history_frame_append("block_changed", (block, event))
		for listener in self.__listeners :
			listener.block_changed(block, event)

	def __on_connection_added(self, sb, st, tb, tt, deserializing=False) :
		
		for listener in self.__listeners :
			listener.connection_added(sb, st, tb, tt, deserializing)

	def __on_connection_removed(self, sb, st, tb, tt) :
		for listener in self.__listeners :
			listener.connection_removed(sb, st, tb, tt)

	def __on_connection_changed(self, sb, st, tb, tt) :
#		raise Exception("not implemented")
		for listener in self.__listeners :
			listener.connection_changed(sb, st, tb, tt)

	# ---------------------------------------------------------------------------------

	def undo(self) :
		if self.__history :
			frame = self.__history.pop()
			self.__redo_stack.insert(0, frame)
			self.__revert_frame(frame)

	perform = {
		"connection_added" : lambda self, data: self.remove_connection(*data),
		"connection_removed" : lambda self, data: self.add_connection(*data[0], meta=data[1]),
		"connection_meta" : lambda self, data: self.set_connection_meta(*data),
		"block_removed" : lambda self, data: self.add_block(data[0]),
		"block_added" : lambda self, data: self.remove_block(data[0]),
		"block_meta" : lambda self, data: None,
	}

	def __revert_frame(self, frame) :
		self.__editing = False #TODO redo, swap stacks
		for act, data in frame :
			GraphModel.perform[act](self, data)

	#XXX do i really want to have logic of history logging in _this_ class?!
	#XXX XXX XXX probably its enough to log changes in model and frame them in editor actions
	def __history_frame_append(self, action, data) :
		self.__assert_editing()
		if self.__history_frame == None:#XXX should not happen because of __assert_editing
#			print "no opened frame"
			pass
		else :
			self.__history_frame.insert(0, (action, data))

	def begin_edit(self) :
#		traceback.print_stack()
		self.__editing = True
		if not self.__history_frame_depth :
#			self.__history_frame_depth = 0
			self.__history_frame = []
#			print "frame opened"
		self.__history_frame_depth += 1
#		print self.__history_frame
#		self.__history_frame = []

	def end_edit(self) :
#		print "end_edit"
		self.__history_frame_depth -= 1 if self.__history_frame_depth else 0
#		self.__history_frame = None
		if not self.__history_frame_depth :
#			print "frame closed", self.__history_frame
			self.__history.append(self.__history_frame)
			self.__history_frame_depth = 0
#			self.__history_frame = []
			self.__history_frame = None
			self.__editing = False

	def __assert_editing(self) :
		if self.__enable_logging and not self.__editing :
#			raise Exception("not editing")
			pass

	def __set_enable_logging(self, v) :
		self.__enable_logging = v

	enable_logging = property(lambda self: self.__enable_logging, __set_enable_logging)

	# ---------------------------------------------------------------------------------

	def enum(self, deserializing=False) :
		for block in self.__blocks :
			self.__on_block_added(block)
		for src, targets in self.__connections.items() :
			for dst in targets :
			 	self.__on_connection_added(*(src + dst), deserializing=deserializing)

	blocks = property(lambda self: self.__blocks)

	connections = property(lambda self: self.__connections)

	listeners = property(lambda self: self.__listeners)

	connections_meta = property(lambda self: self.__connections_meta)

	def __init__(self) :

		self.__history_frame_depth = 0 #XXX equals bool(self.__editing)
		self.__history_frame = None
		self.__history = []
		self.__editing = False
		self.__enable_logging = True

		self.__blocks = []
		self.__connections = {}
		self.__listeners = []
		self.__connections_meta = {}

# ------------------------------------------------------------------------------------------------------------

class BlockPrototype(object) :

	# to be shown in bloced
	type_name = property(lambda self: self.__type_name)

	# to be used in code to execute block
	exe_name = property(lambda self: self.__exe_name)

	terms = property(lambda self: self.__terms)
	
	category = property(lambda self: self.__category)
	
	default_size = property(lambda self: self.__default_size)

	def __init__(self, type_name, terms, exe_name = None, default_size=(64,64), category="all") :
		self.__category = category
		#TODO return self.type_name if not self.exe_name else self.exe_name
		self.__type_name, self.__terms, self.__default_size, self.__exe_name = (
			type_name, terms, default_size, exe_name )

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
	def __init__(self) :
		BlockPrototype.__init__(self, "DelayIn", [ In("x", W, 0.5) ],
			default_size=(96,28))

class DelayOutProto(BlockPrototype):
	def __init__(self) :
		BlockPrototype.__init__(self, "DelayOut", [ Out("y", E, 0.5) ],
			default_size=(96,28))

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
			NoteProto(),

			SBP("xor", "Logic", [ In("a", W, 0.333), In("b", W, 0.666), Out("y", E, 0.5) ]),
			SBP("or", "Logic", [ In("a", W, 0.333), In("b", W, 0.666), Out("y", E, 0.5) ]),
			SBP("nor", "Logic", [ In("a", W, 0.333), In("b", W, 0.666), Out("y", E, 0.5) ]),
			SBP("and", "Logic", [ In("a", W, 0.333), In("b", W, 0.666), Out("y", E, 0.5) ]),
			SBP("nand", "Logic", [ In("a", W, 0.333), In("b", W, 0.666), Out("y", E, 0.5) ]),
			SBP("not", "Logic", [ In("a", W, 0.5), Out("y", E, 0.5) ]),

			SBP("add", "Arithmetic", [ In("a", W, 0.333), In("b", W, 0.666), Out("y", E, 0.5) ]),
			SBP("sub", "Arithmetic", [ In("a", W, 0.333), In("b", W, 0.666), Out("y", E, 0.5) ]),
			SBP("mul", "Arithmetic", [ In("a", W, 0.333), In("b", W, 0.666), Out("y", E, 0.5) ]),
			SBP("div", "Arithmetic", [ In("n", W, 0.333), In("d", W, 0.666), Out("y", E, 0.5) ]),
			SBP("mod", "Arithmetic", [ In("n", W, 0.333), In("d", W, 0.666), Out("y", E, 0.5) ]),
			SBP("divmod", "Arithmetic", [ In("n", W, 0.333), In("d", W, 0.666),
				Out("q", E, 0.333), Out("r", E, 0.666)  ]),

			SBP("load", "Memory", [ ]),
			SBP("store", "Memory", [ ]),
			SBP("load_nv", "Memory", [ ]),
			SBP("store_nv", "Memory", [ ]),

			SBP("di", "Process IO", [ In("nr", W, 0.5), Out("y", E, 0.5) ], exe_name="io.di"),
			SBP("do", "Process IO", [ In("nr", W, 0.333), In("x", W, 0.666) ], exe_name="io.do"),
		]

# ------------------------------------------------------------------------------------------------------------

def create_block_factory() :
	return BasicBlocksFactory()

# ------------------------------------------------------------------------------------------------------------

