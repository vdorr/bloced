
from itertools import dropwhile, islice, count
#import traceback

"""
serialiazable model of graph, part of editor bussiness logic, definitions for presentation layer
"""

# ------------------------------------------------------------------------------------------------------------

#TODO replace usages of Tkinter stuff elsewhere
C = "C"
N = "n"
S = "s"
W = "w"
E = "e"

INPUT_TERM = 1
OUTPUT_TERM = 2

term_size = 8

# ------------------------------------------------------------------------------------------------------------

class TermModel(object) :

#	def get_location_on_blockDEPRECATED(self, bm, n) :

##		m = bm.get_term_multiplicity(self)
##		(x, y), _ = bm.get_term_and_lbl_pos(self, n, 0, 0)

#		xo, yo = bm.left, bm.top
#		p = self.get_pos(bm)

#		c = 0
##		if self.variadic :
##			if m > 1 :
##				c = (m - 1) * term_size

#		sides = { #TODO precompute/add args to lambda/make class member
#			N : lambda: (int(xo + p * bm.width)+c, yo),
#			S : lambda: (int(xo + p * bm.width)+c, yo + bm.height),
#			W : lambda: (xo, int(yo + p * bm.height)+c),
#			E : lambda: (xo + bm.width, int(yo + p * bm.height)+c),
#			C : lambda: (xo + 0.5 * bm.width, int(yo + 0.5 * bm.height)),
#		}
#		retval = sides[self.get_side(bm)]()
##		print "get_location_on_block:", (x+xo, y+yo), " vs.", retval
#		return retval

	def get_side(self, bm) :
		flipv, fliph, rot = bm.orientation
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

	def get_pos(self, bm) :
		x, y, _ = bm.orientation
		return (1 - self.__pos) if x or y else self.__pos

	name = property(lambda self: self.__name)

	default_side = property(lambda self: self.__side)

	default_pos = property(lambda self: self.__pos)

	direction = property(lambda self: self.__direction)

	type_name = property(lambda self: self.__type_name)

	variadic = property(lambda self: self.__variadic)

	commutative = property(lambda self: self.__commutative)

	def __init__(self, arg_index, name, side, pos, direction, variadic, commutative, type_name=None) :
#		self.__name, self.__side, self.__pos, self.__direction, self.__type_name = (
#			name, side, pos, direction, type_name )
		self.__name = name
		self.__side = side
		self.__pos = pos
		self.__direction = direction
		self.__type_name = type_name
		self.arg_index = arg_index
		self.__variadic = variadic
		self.__commutative = commutative

	def __repr__(self) :
		return "." + self.__name
#		return hex(id(self)) + " " + {INPUT_TERM:"in",OUTPUT_TERM:"out"}[self.direction] + ":" + self.name

class In(TermModel) :
	def __init__(self, arg_index, name, side, pos, type_name=None, variadic=False, commutative=False) :
		TermModel.__init__(self, arg_index, name, side, pos, INPUT_TERM, variadic, commutative)

class Out(TermModel) :
	def __init__(self, arg_index, name, side, pos, type_name=None, variadic=False, commutative=False) :
		TermModel.__init__(self, arg_index, name, side, pos, OUTPUT_TERM, variadic, commutative)

# ------------------------------------------------------------------------------------------------------------

class BlockModel(object) :

	def __lt__(self, other):
		return id(other) < id(self)

	class edit(object) :
	
		def __init__(self, prop_name) :
			self.prop_name = prop_name
		
		def __call__(self, f) :
			def decorated(*v, **w) :
				old_meta = { self.prop_name : v[0].get_meta()[self.prop_name] }
				y = f(*v, **w)
				new_meta = { self.prop_name : v[0].get_meta()[self.prop_name] }
				v[0]._BlockModel__raise_block_changed({"p":self.prop_name}, new_meta=new_meta, old_meta=old_meta)
				return y
			return decorated

	def __raise_block_changed(self, e, old_meta=None, new_meta=None) :
		self.__model._GraphModel__on_block_changed(self, event=e, old_meta=old_meta, new_meta=new_meta)

	@edit("value")
	def __set_value(self, value) :
		self.__value = value
#		if self.value :
#			self.caption = self.prototype.get_type_name() + " (" + str(self.value) + ")"
#		self.__raise_block_changed({"p":"value"})
#		self.__model._GraphModel__on_block_changed(self, event=e)

	int_left = property(lambda self: self.__left)

	int_top = property(lambda self: self.__top)

	value = property(lambda self: self.__value, __set_value)

	@edit("caption")
	def __set_caption(self, v) :
		self.__set_caption = v
#		self.__raise_block_changed({"p":"caption"})

	caption = property(lambda self: self.__caption, __set_caption)

	def get_meta(self) :
		w, h = self.prototype.default_size
		return {
			"caption" : self.caption,
			"left" : self.left,
			"top" : self.top,
			"width" : w,
			"height" : h,
#			"width" : self.width,
#			"height" : self.height,
			"value" : self.value,
			"orientation" : self.orientation,
			"term_meta" : self.__term_meta,
		}

	def set_meta(self, meta) :
		for k, v in meta.items() :
			self.__getattribute__("_BlockModel__set_"+k)(v)
			self.__raise_block_changed({"p":k})

	def __set_term_meta(self, meta) :
		self.__term_meta = meta
#		print "__set_term_meta:", 

	@edit("term_meta")
	def stme(self, term, n):
		self.__term_meta[term.name]["multiplicity"] = n

	def set_term_multiplicity(self, term, n, no_events=False) :
		if not term.variadic :
			raise Exception("set_term_multiplicity: terminal is not variadic")
		if no_events :
			self.__term_meta[term.name]["multiplicity"] = n
		else :
			self.stme(term, n)

	def get_term_multiplicity(self, term) :
		return self.__term_meta[term.name]["multiplicity"] if term.variadic else None

	terms = property(lambda self: self.__terms)#XXX return copy instead of my instance?

	def __get_orientation(self) :
		return self.__orientation

	@edit("orientation")
	def __set_orientation(self, v) :
		self.__orientation = v
#		self.__raise_block_changed({"p":"orientation"})

	orientation = property(__get_orientation, __set_orientation)

	default_size = property(lambda self: (self.__get_default_width(), self.__get_default_height()))

	def __get_default_height(self) :
		return self.__width if self.orientation[2] % 180 else self.__height

	def __get_default_width(self) :
		return self.__height if self.orientation[2] % 180 else self.__width

	def __get_width(self) :
		return self.__get_prop_height() if self.orientation[2] % 180 else self.__get_prop_width()

	@edit("width")
	def __set_width(self, v) :
		if self.orientation[2] % 180 :
			self.__height = v
		else :
			self.__width = v
#		self.__raise_block_changed({"p":"width"})

	def __get_prop_height(self) :
		l = self.__height
		trms = [ t for t in self.terms if t.default_side in (W, E) ]
		varterms = sum([ self.get_term_multiplicity(t)-1 if t.variadic else 0 for t in trms ])
		return l + varterms * term_size

	def __get_prop_width(self) :
		l = self.__width
		trms = [ t for t in self.terms if t.default_side in (N, S) ]
		varterms = sum([ self.get_term_multiplicity(t)-1 if t.variadic else 0 for t in trms ])
		return l + varterms * term_size

	def __get_height(self) :
		return self.__get_prop_width() if self.orientation[2] % 180 else self.__get_prop_height()

	@edit("height")
	def __set_height(self, v) :
		if self.orientation[2] % 180 :
			self.__width = v
		else :
			self.__height = v
#		self.__raise_block_changed({"p":"height"})

	def __get_left(self) :
		return self.__left + ((self.__width - self.__height) / 2 if self.orientation[2] % 180 else 0)

	@edit("left")
	def __set_left(self, v) :
		self.__left = v - ((self.__width - self.__height) / 2 if self.orientation[2] % 180 else 0)
#		self.__raise_block_changed({"p":"left"})

	def __get_top(self) :
		return self.__top + ((self.__height - self.__width) / 2 if self.orientation[2] % 180 else 0)

	@edit("top")
	def __set_top(self, v) :
		self.__top = v - ((self.__height - self.__width) / 2 if self.orientation[2] % 180 else 0)
#		self.__raise_block_changed({"p":"top"})

	def __get_center(self) :
		return self.left+(self.width/2), self.top+(self.height/2)

	def __set_center(self, v) :
		self.left = v[0] - (self.width/2)
		self.top = v[1] - (self.height/2)

	width = property(__get_width, __set_width)

	height = property(__get_height, __set_height)

	left = property(__get_left, __set_left)

	top = property(__get_top, __set_top)

	center = property(__get_center, __set_center)

	prototype = property(lambda self: self.__prototype)

#XXX XXX XXX
	def get_term_index(self, t, t_nr) :
		index = self.__term_meta[t.name][t_nr, "index"]
#		print "get_term_index:", self, t.name, t_nr, index
		return index

	def get_indexed_terms(self, t) :
		#self.__term_meta[t.name][t_nr, "index"]
		return [ (k[0], v) for k, v in self.__term_meta[t.name].items()
			if type(k) == tuple and type(k[0]) == int and k[1] == "index" ]

#XXX XXX XXX
	def set_term_index(self, t, t_nr, index) : # index would be usually term_multiplicity-1
		self.__term_meta[t.name][t_nr, "index"] = index
#		print "set_term_index:", self.__term_meta

#XXX XXX XXX
	def pop_term_meta(self, t, t_nr) :
		if (t_nr, "index") in self.__term_meta[t.name] :
			self.__term_meta[t.name].pop((t_nr, "index")) #and also the rest, if ever some rest will be
#			self.__term_meta.pop((t.name, t_nr, "index")) #and also the rest, if ever some rest will be

	def get_term_location(self, t, t_nr) :
#		print "get_term_location:", t, t_nr
#		retval = t.get_location_on_blockDEPRECATED(self, t_nr)
		(x, y), _ = self.get_term_and_lbl_pos(t, t_nr, 0, 0, center=False)
#		print "get_term_location:", retval, " vs.", (x+self.left, y+self.top)
		return (x+self.left, y+self.top)
#		assert(retval==...
#		return retval

	def get_term_and_lbl_pos(self, t, t_nr, text_width, txt_height, center=True) :

#		dw, dh = self.__prototype.default_size

		t_size = term_size
		shift = t_size/2 if center else 0
#XXX XXX XXX
#		index = t_nr
		index = self.get_term_index(t, t_nr) if t.variadic else 1
		c = (index - 1) * term_size if t.variadic else 0
#XXX XXX XXX
		#TODO precompute
##		sides = {
##			N : lambda p, tw: ((self.width*p-t_size/2+c, 0), (0, t_size)),
##			S : lambda p, tw: ((self.width*p-t_size/2+c, self.height-t_size-1), (0, -t_size)),
##			W : lambda p, tw: ((0, self.height*p-t_size/2+c), (t_size, 0)),
##			E : lambda p, tw: ((self.width-t_size-1, self.height*p-t_size/2+c), (-1-tw, 0)),
##			C : lambda p, tw: ((0.5*self.width, 0.5*self.height), (0, 0)),
##		}
#		sides = {
#			N : lambda p, tw: ((self.width*p-shift+c, 0), (0, t_size)),
#			S : lambda p, tw: ((self.width*p-shift+c, self.height-t_size-1), (0, -t_size)),
#			W : lambda p, tw: ((0, self.height*p-shift+c), (t_size, 0)),
#			E : lambda p, tw: ((self.width-t_size-1, self.height*p-shift+c), (-1-tw, 0)),
#			C : lambda p, tw: ((self.width/2, self.height/2), (0, 0)),
#		}
		p = t.get_pos(self)
		tw = text_width
		side = t.get_side(self)

		if t.variadic :
			w, h = self.width, self.height
		else :
			w, h = self.default_size

		if side == N :
			pos = ((w*p-shift+c, 0),		(0, t_size))
		elif side == S :
#			pos = ((w*p-shift+c, h-t_size-1),	(0, -t_size))
			pos = ((w*p-shift+c, h-1),	(0, -t_size))
		elif side == W :
			pos = ((0, h*p-shift+c),		(t_size, 0))
		elif side == E :
#			pos = ((w-t_size-1, h*p-shift+c),	(-1-tw, 0))
			pos = ((w-1, h*p-shift+c),	(-1-tw-t_size, 0))
#			pos = ((w-1, h*p-shift+c),	(-1-tw, 0))
		elif side == C :
			pos = ((w/2, h/2),			(0, 0))
		else :
			raise Exception()

		#XXX XXX (x, y), (txtx, txty) = 
		(x, y), (txtx, txty) = pos#sides[t.get_side(self)](t.get_pos(self), text_width)
		return (x, y), (x+txtx, int(y-(0.2*txt_height)+txty))

#	def __get__connections(self) :
##		print self.__graph.connections
#		return None#self.__graph.connections.iteritems()

#	connections = property(__get__connections)

	def get_terms_flat(self) :
		for t in self.terms :
			if t.variadic :
#				iterms = sorted(self.get_indexed_terms(t), key=lambda x: x[1])#sort by index
				for nr, index in sorted(self.get_indexed_terms(t), key=lambda x: x[1]) :
					yield t, nr
#				m = self.get_term_multiplicity(t)
#				if m > 1 :
#					for nr in range(m) :
#						yield t, nr
#				else :
#					yield t, 0
			else :
				yield t, None

	def get_presentation_text(self) :
		if self.prototype.__class__.__name__ == "ConstProto" :
			newtxt = self.value
		elif self.prototype.__class__.__name__ == "DelayProto" :
			newtxt = "Delay (%s)" % self.value if self.value != None else "None"
		elif self.prototype.__class__.__name__ == "JointProto" :
			newtxt = ""
		else :
			newtxt = self.caption
		return newtxt

	presentation_text = property(get_presentation_text)

	def get_term_presentation_text(self, t, nr) :
		term_label = t.name
		if self.prototype.__class__.__name__ == "ConstProto" :
			term_label = ""#str(self.model.value)
		if t.variadic : #XXX nr != None
			term_label += str(self.get_term_index(t, nr))
		return term_label

	def __my_init(self, model, caption, left, top, width, height, terms) :
		self.__orientation = (0, 0, 0)
		self.__caption, self.__left, self.__top, self.__width, self.__height, self.__terms = (
			caption, left, top, width, height, terms)
		self.__model = model
		self.__can_move = True
		self.__prototype = None
		self.__value = None
		self.__term_meta = { t.name: { "multiplicity" : 1, (0, "index") : 0 } for t in terms if t.variadic }

	def __init__(self, prototype, model, left = 0, top = 0) :
#		print prototype.default_size
		self.__my_init(model, prototype.type_name, left, top,
			prototype.default_size[0], prototype.default_size[1],
			prototype.terms)
		self.__prototype = prototype

	def __repr__(self) :
#		return self.__prototype.type_name
		return "%s(%s)" % (self.__prototype.type_name, str(self.value))
		#return "block proto=" + type(self.prototype).__name__
		#return 'block"' + self.prototype.type_name + '"'
#		return hex(id(self)) + " " + 'blck"' + self.__caption + '"'# + str(id(self))

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

	def get_meta(self) :
		return {} # TODO implement it and make it property

#	def set_meta(self) :
#		self.__assert_editing()
#		pass # TODO implement it and make it property

#	meta = property(lambda self: {})

	def add_listener(self, listener) :
		self.__listeners.append(listener)

	def remove_listener(self, listener) :
		self.__listeners.remove(listener)

	# ---------------------------------------------------------------------------------

#	def set_block_meta(self, block, meta) :
#		for k, v in meta.iteritems() :
#			self.__getattribute__("_BlockModel__set_"+k)(v)
#			self.__raise_block_changed({"p":k})

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
#		print "can_connect:", sb, st, tb, tt
#TODO if variadic check max count
		st, sn = st if isinstance(st, tuple) else (st, 0)
		tt, tn = tt if isinstance(tt, tuple) else (tt, 0)
		return (st.direction != tt.direction and
			st.direction in (INPUT_TERM, OUTPUT_TERM) and
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


	def __variadic_term_test(self, t, t_tst) :
		return isinstance(t_tst, tuple) and t_tst[0] == t


	def __add_variadic_term(self, block, term, deserializing=False) :
		assert(term.variadic)
		iterms = sorted(block.get_indexed_terms(term), key=lambda x: x[1])#sort by index
		if not deserializing :
			new_nr = 0
			for nr, _ in sorted(iterms, key=lambda x: x[0]) :
				if nr != new_nr :
					break
				new_nr += 1
			m = block.get_term_multiplicity(term)#XXX base this on get_indexed_terms?
			assert(len(iterms) == m)
#			print "__add_variadic_term: new_nr=", new_nr, "m=", m, "indexed terms:", iterms
			block.set_term_index(term, new_nr, m)
			block.set_term_multiplicity(term, m+1, no_events=False)
			term_number = iterms[-1][0]
#			print "__add_variadic_term: m(2)=", block.get_term_multiplicity(term)
#		print "__add_variadic_term(3): ", iterms[-1][0], block.get_indexed_terms(term)
		return None, (term, term_number)


	def add_connection(self, b0, t0, b1, t1, meta={}, deserializing=False) :
#		print "add_connection: ", b0, t0, b1, t1
		if not deserializing :

			if not self.can_connect(b0, t0, b1, t1) :#TODO add multiplicity
				raise Exception("can't connect")
#			print "add_connection:", b0, t0, b1, t1
			b0, t0, b1, t1 = (b0, t0, b1, t1) if t0.direction == OUTPUT_TERM else (b1, t1, b0, t0)

			if not isinstance(t0, tuple) and t0.variadic :
	#			print "add_connection 1"
				m0, t0 = self.__add_variadic_term(b0, t0, deserializing=deserializing)
			if not isinstance(t1, tuple) and t1.variadic :
	#			print "add_connection 2"
				m1, t1 = self.__add_variadic_term(b1, t1, deserializing=deserializing)

		if (b0, t0) in self.__connections :
			self.__connections[(b0, t0)].append((b1, t1))
		else :
			self.__connections[(b0, t0)] = [(b1, t1)]
		self.connections_meta[(b0, t0, b1, t1)] = meta

		self.__history_frame_append("connection_added", ((b0, t0, b1, t1), meta))
		self.__on_connection_added(b0, t0, b1, t1, deserializing=deserializing)


	def __remove_variadic_term(self, block, term, number) :
		assert(term.variadic)
		iterms = sorted(block.get_indexed_terms(term), key=lambda x: x[1])#sort by index
		m = block.get_term_multiplicity(term)#XXX base this on get_indexed_terms?
		assert(len(iterms) == m)
		block.pop_term_meta(term, number)
#		print "__remove_variadic_term:", number, m, iterms
		new_index = 0
		for nr, index in iterms :
			if nr != number :
#				print "__remove_variadic_term(2):", term, nr, new_index
				block.set_term_index(term, nr, new_index)
				new_index += 1
#		print "__remove_variadic_term(3):", block.get_indexed_terms(term)
		block.set_term_multiplicity(term, m-1, no_events=True)


	def remove_connection(self, b0, t0, b1, t1) :
		t0t, n0 = t0 if isinstance(t0, tuple) else (t0, 0)
		t1t, n1 = t1 if isinstance(t1, tuple) else (t1, 0)

		i = self.__connections[(b0, t0)]
		i.remove((b1, t1))
		if not i :
			self.__connections.pop((b0, t0))
		meta = None
		if (b0, t0, b1, t1) in self.__connections_meta :
			meta = self.__connections_meta.pop((b0, t0, b1, t1))

		if t0t.variadic :
			self.__remove_variadic_term(b0, t0t, n0)
		if t1t.variadic :
			self.__remove_variadic_term(b1, t1t, n1)

		self.__history_frame_append("connection_removed", ((b0, t0, b1, t1), meta))
		self.__on_connection_removed(b0, t0, b1, t1)
#		self.__on_block_changed(self, b0)
#		self.__on_block_changed(self, b1)


	# ---------------------------------------------------------------------------------

	def __on_block_added(self, block) :
		for listener in self.__listeners :
			listener.block_added(block)

	def __on_block_removed(self, block) :
		for listener in self.__listeners :
			listener.block_removed(block)

	def __on_block_changed(self, block, event=None, old_meta=None, new_meta=None) :
		self.__history_frame_append("block_meta", (block, old_meta))
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
		if self.__undo_stack :
			frame = self.__undo_stack.pop()
#			self.__redo_stack.append(frame)
			self.__revert_frame(frame)

#XXX swap stacks and log?
	def redo(self) :
		pass
#		if self.__redo_stack :
#			frame = self.__redo_stack.pop()
#			self.__undo_stack.append(frame)
#			self.__revert_frame(frame)

	inverse_actions = {
		"connection_added" : lambda self, data: self.remove_connection(*data),
		"connection_removed" : lambda self, data: self.add_connection(*data[0], meta=data[1]),
		"connection_meta" : lambda self, data: self.set_connection_meta(*data),
		"block_removed" : lambda self, data: self.add_block(data[0]),
		"block_added" : lambda self, data: self.remove_block(data[0]),
		"block_meta" : lambda self, data: data[0].set_meta(data[1]),
	}

	def __revert_frame(self, frame) :
		self.__editing = False #TODO redo, swap stacks
		for act, data in frame :
			GraphModel.inverse_actions[act](self, data)

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
			self.__undo_stack.append(self.__history_frame)
#			self.__history_frame_depth = 0
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

#	listeners = property(lambda self: self.__listeners)

	connections_meta = property(lambda self: self.__connections_meta)

	def __init__(self) :

		self.__history_frame_depth = 0 #XXX equals bool(self.__editing)
		self.__history_frame = None
		self.__undo_stack = []
		self.__redo_stack = []
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

	inputs = property(lambda self: [ t for t in self.__terms if t.direction == INPUT_TERM ] )

	outputs = property(lambda self: [ t for t in self.__terms if t.direction == OUTPUT_TERM ] )
	
	category = property(lambda self: self.__category)
	
	default_size = property(lambda self: self.__default_size)

	commutative = property(lambda self: self.__commutative)

	pure = property(lambda self: self.__pure)

	def __init__(self, type_name, terms,
			exe_name = None,
			default_size = (64,64),
			category = "all",
			commutative = False,
			pure = False) :
		self.__category = category
		#TODO return self.type_name if not self.exe_name else self.exe_name
		self.__type_name = type_name
		self.__terms = terms
		self.__default_size = default_size
		self.__exe_name = exe_name
		self.__commutative = commutative
		self.__pure = pure

# ------------------------------------------------------------------------------------------------------------

