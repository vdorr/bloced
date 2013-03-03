
"""
serialiazable model of graph, part of editor bussiness logic, definitions for presentation layer
"""

from sys import version_info

if version_info.major == 3 :
	from functools import reduce
	from io import StringIO
	from queue import Queue, Empty as QueueEmpty
else :
	from Queue import Queue, Empty as QueueEmpty
	from StringIO import StringIO

from threading import Thread, Lock
import time
import sys
import os
from sys import version_info
from pprint import pprint
from itertools import dropwhile, islice, count
#from collections import namedtuple
import traceback

import core
import build
import ccodegen
import implement
import serializer
from utils import here
import mathutils
import gateway


# ------------------------------------------------------------------------------------------------------------


class EditorInterface(object) :
	"""
	draft interface for generic editor to allow support of different types of resources in workbench
	"""

	def get_capabilities(self) :
		return {}

	def get_editor_class(self) :
		return "bloced", "LibraryMetadataEditor" #for example

	def get_changed(self) : pass
	def undo(self) : pass
	def redo(self) : pass
	def get_selection(self) : pass
	def clear_selection(self) : pass
	def cut(self) : pass
	def copy(self) : pass
	def paste(self) : pass
	def delete(self) : pass


class GraphModelListener(object) :
	"""
	interface for GraphModel-events consuming object
	"""
	def block_added(self, sheet, block) : pass
	def block_removed(self, sheet, block) : pass
	def block_changed(self, sheet, block, event=None) : pass
	def connection_added(self, sheet, sb, st, tb, tt, deserializing=False) : pass
	def connection_removed(self, sheet, sb, st, tb, tt) : pass
	def connection_changed(self, sheet, sb, st, tb, tt) : pass #TODO monitoring etc.
	def meta_changed(self, sheet, key, key_present, old_value, new_value) : pass


# ------------------------------------------------------------------------------------------------------------

#TODO replace usages of Tkinter stuff elsewhere
C = "C"
N = "n"
S = "s"
W = "w"
E = "e"

#XXX these consts must go!

TERM_SIZE = 11

#for macroes and foreign functions
MIN_BLOCK_WIDTH = 96
MIN_BLOCK_HEIGHT = 64

# ------------------------------------------------------------------------------------------------------------

#def get_term_poly(tx, ty, tsz, side, direction, txt_width) :
##TODO try to rotate around center of block
#	txt_height = tsz
#	ang = { N : 90, S : 270, W : 0, E : 180, C : 0, }
#	txt_width += (0 if direction == core.INPUT_TERM else tsz)
#	shift = { N : (0, 0), S : (0, txt_width+1), W : (0, 0), E : (txt_width+1, 0), C : (0, 0), }
#	sx, sy = shift[side]
#	glyph = ( (tx-sx, ty-1-sy),
#		(tx+1+txt_width-sx, ty-1-sy),
#		(tx+txt_width-sx+1+(tsz/2 if direction == core.INPUT_TERM else -tsz/2), ty-sy+tsz/2),
#		(tx+1+txt_width-sx, ty+tsz-sy+1),
#		(tx-sx, ty+tsz-sy+1) )
#	l, t, w, h = mathutils.bounding_rect(glyph)
#	orgx = l + 0.5 * w
#	orgy = t + 0.5 * h
#	a = (ang[side]) % 360
#	sin_angle, cos_angle = mathutils.rotate4_trig_tab[a]
#	def r(xx, yy) :
#		return (orgx + ((xx - orgx) * cos_angle - (yy - orgy) * sin_angle),
#			orgy + ((xx - orgx) * sin_angle + (yy - orgy) * cos_angle))
#	return tuple(r(*p) for p in glyph)

def translate(sx, sy, p) :
	return tuple((x+sx, y+sy) for x, y, in p)

def get_glyph(w, h, direction) :
	tip = ((h/2) if direction == core.INPUT_TERM else (-h/2))
	w += (0 if direction == core.INPUT_TERM else (h/2))
	return ( (0, 0), (w, 0), (w+tip, h/2), (w, h), (0, h) )

#XXX try caching decorator on this?
def get_term_poly(tx, ty, txt_height, side, direction, txt_width) :
	ang = {
		N : 90,
		S : 270,
		W : 0,
		E : 180,
		C : 0,
	}
#	txt_width += (0 if direction == core.INPUT_TERM else txt_height)
	txt_width += txt_height / 2
	shift = {
		N : (0, 0),
		S : (0, txt_width+1),
		W : (0, 0),
		E : (txt_width+txt_height/2+1, 0),
#		E : (txt_width+10, 0),
		C : (0, 0),
	}

	sx, sy = shift[side]

#	glyph = ( (tx-sx, ty-1-sy),
#		(tx+1+txt_width-sx, ty-1-sy),
#		(tx+txt_width-sx+1+(txt_height/2 if direction == core.INPUT_TERM else -txt_height/2), ty-sy+txt_height/2),
#		(tx+1+txt_width-sx, ty+txt_height-sy+1),
#		(tx-sx, ty+txt_height-sy+1) )

	g = get_glyph(txt_width, txt_height+1, direction)
#	print(here(), g)
	glyph = translate(tx-sx, ty-sy, g)
#	print(here(), glyph)

#	print here(), txt_width, txt_height

	l, t, w, h = mathutils.bounding_rect(glyph)

	orgx = l + 0.5 * w
	orgy = t + 0.5 * h

	a = (ang[side]) % 360

	sin_angle, cos_angle = mathutils.rotate4_trig_tab[a]

	def r(xx, yy) :
		return (orgx + ((xx - orgx) * cos_angle - (yy - orgy) * sin_angle),
			orgy + ((xx - orgx) * sin_angle + (yy - orgy) * cos_angle))

	g2 = tuple(r(*p) for p in glyph)

	return g2

# ------------------------------------------------------------------------------------------------------------


class edit(object) :

	def __init__(self, prop_name=None) :
		self.prop_name = prop_name

	def __call__(self, f) :
		def decorated(*v, **w) :
			old_meta = { self.prop_name : v[0].get_meta()[self.prop_name] }
			y = f(*v, **w)
			new_meta = { self.prop_name : v[0].get_meta()[self.prop_name] }
			v[0]._BlockModel__raise_block_changed({"p":self.prop_name}, old_meta, new_meta)
			return y
		return decorated


class BlockModelData(object) :


	prototype = property(lambda self: self.__prototype)


	def __lt__(self, other):
		return id(other) < id(self)


	terms = property(lambda self: self.__terms)#XXX return copy instead of my instance?


	def __init__(self, prototype, model) :
		self.__prototype = prototype
		self.__terms = prototype.terms


class BlockModel(BlockModelData) :


	def to_string(self) :
		return "%s(%s)" % (self.prototype.type_name, str(self.value))


	def get_term_side(self, t) :
		flipv, fliph, rot = self.orientation
		ors = {
			W: 2 if fliph else 0,
			N: 3 if flipv else 1,
			E: 0 if fliph else 2,
			S: 1 if flipv else 3
		}
		if t.default_side != C :
			old_or = ors[t.default_side]
			side = [ W, N, E, S ][ (ors[t.default_side] + rot // 90) % 4 ]
			return side
		return t.default_side


	def get_term_pos(self, t) :
		x, y, _ = self.orientation
		return (1 - t.default_pos) if x or y else t.default_pos


#	def get_term_and_lbl_pos_NEW(self, t, t_nr, term_width, term_height, center=True) :
#		same_side_terms = tuple(sorted((term for term, _ in self.get_terms_flat() if term.direction == t.direction), key=lambda term: term.default_pos))
#		w, h = self.width, self.height

#		side = self.get_term_side(t)

#		if side in (N, S) :
#			a = w
#		elif side in (W, E) :
#			a = h
#		elif side == C :
#			return (w/2, h/2), (0, 0)
#		else :
#			raise Exception()


#		term_index = self.get_term_index(t, t_nr) if t.variadic else 1
#		side_index = same_side_terms.index(t)
#		(side_index + term_index) * term_height + (len(same_side_terms) / 2) * term_height


	def get_term_and_lbl_pos(self, t, t_nr, text_width, txt_height, center=True) :

#		self.get_term_and_lbl_pos_NEW(t, t_nr, text_width, txt_height, center=center)

#		dw, dh = self.__prototype.default_size

		t_size = txt_height#XXX may depend on orientation
		shift = t_size/2 if center else 0
#XXX XXX XXX
#		index = t_nr
		index = self.get_term_index(t, t_nr) if t.variadic else 1

#		print here(), t.name, t_nr, self.get_term_index(t, t_nr) if t.variadic else 666

		c = (((index - 0) * t_size)) if t.variadic else 0
#XXX XXX XXX

		p = self.get_term_pos(t)
		tw = text_width
		side = self.get_term_side(t)

#		if t.variadic :
#			w, h = self.width, self.height
#		else :
#			w, h = self.default_size
		w, h = self.default_size

		if side == N :
			pos = ((w*p-shift+c, 0),	(0, 0))
		elif side == S :
			pos = ((w*p-shift+c, h-1),	(0, 0))
		elif side == W :
			pos = ((0, h*p-shift+c),	(0, 0))
		elif side == E :
			pos = ((w-1, h*p-shift+c),	(-1-tw, 0))
		elif side == C :
			pos = ((w/2, h/2),		(0, 0))
		else :
			raise Exception()

		#XXX XXX (x, y), (txtx, txty) = 
		(x, y), (txtx, txty) = pos#sides[t.get_side(self)](t.get_pos(self), text_width)
#		txtx, txty = 0, 0
#		print(here(), x, y, self.width, self.height)

#		return (int(x), int(y)), (x+txtx, int(y-(0.2*txt_height)+txty))
		return (int(x), int(y)), (int(x+txtx), int(y+txty))


	def get_term_location(self, t, t_nr, text_width, text_height) :
		(x, y), _ = self.get_term_and_lbl_pos(t, t_nr, text_width, text_height, center=False)
		return (x+self.left, y+self.top)


	def get_label_pos(self, txt_width, txt_height) :
		side =  [W, N, E, S][self.orientation[2]//90]
		if side == W :
			pos = (0, 0)
		elif side == N :
			pos = (self.width-txt_height, 0)
		elif side == E :
			pos = (self.width-txt_width, self.height-txt_height)
		elif side == S :
			pos = (0, self.height-txt_height)
		else :
			raise Exception()
		return pos


	def __raise_block_changed(self, e, old_meta, new_meta) :
		if self.__model == "itentionally left blank" :
			return None
		self.__model._GraphModel__on_block_changed(self, e, old_meta, new_meta)


#	@edit()
	def set_meta(self, meta) :
#		print here(3), meta
		old_meta = self.get_meta()
		for k, v in meta.items() :
			self.__getattribute__("_BlockModel__set_"+k)(v)
			assert(not(k is None))
			self.__raise_block_changed({"p":k}, {k:old_meta[k]}, {k:v})


	@edit("value")
	def __set_value(self, value) :
		if isinstance(value, tuple) :
			self.__value = value
		else :
			self.__value = (value,)


	int_left = property(lambda self: self.__left)


	int_top = property(lambda self: self.__top)


	value = property(lambda self: self.__value, __set_value)


	@edit("caption")
	def __set_caption(self, v) :
		self.__set_caption = v


	caption = property(lambda self: self.__caption, __set_caption)


	def get_instance_id(self) :
		return self.__instance_id


	@edit("instance_id")
	def __set_instance_id(self, value) :
#		print here(), value
		self.__instance_id = value


	def set_instance_id(self, value) :
		self.__set_instance_id(value)


	def get_meta(self) :
		w, h = self.prototype.default_size
		meta = {
			"caption" : self.caption,
			"left" : self.left,
			"top" : self.top,
			"width" : w,
			"height" : h,
			"value" : self.value,
			"orientation" : self.orientation,
			"term_meta" : self.__term_meta,
			"instance_id" : self.get_instance_id(),
		}
		if not core.is_builtin_block(self.prototype)  :
			meta["cached_prototype"] = self.prototype.get_block_proto_data()
		return meta


	def __set_term_meta(self, meta) :
		self.__term_meta = meta


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


	def __get_orientation(self) :
		return self.__orientation


	@edit("orientation")
	def __set_orientation(self, v) :
		self.__orientation = v


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


	def __get_prop_height(self, term_size=13) :
		l = self.__height
		trms = [ t for t in self.terms if t.default_side in (W, E) ]
		varterms = sum(self.get_term_multiplicity(t)-1 if t.variadic else 0 for t in trms)
		return l + varterms * term_size


	def __get_prop_width(self, term_size=13) :
		l = self.__width
		trms = [ t for t in self.terms if t.default_side in (N, S) ]
		varterms = sum(self.get_term_multiplicity(t)-1 if t.variadic else 0 for t in trms)
		return l + varterms * term_size


	def __get_height(self) :
		return self.__get_prop_width() if self.orientation[2] % 180 else self.__get_prop_height()


	@edit("height")
	def __set_height(self, v) :
		if self.orientation[2] % 180 :
			self.__width = v
		else :
			self.__height = v


	def __get_left(self) :
		return self.__left + ((self.__width - self.__height) / 2 if self.orientation[2] % 180 else 0)


	@edit("left")
	def __set_left(self, v) :
		self.__left = v - ((self.__width - self.__height) / 2 if self.orientation[2] % 180 else 0)


	def __get_top(self) :
		return self.__top + ((self.__height - self.__width) / 2 if self.orientation[2] % 180 else 0)


	@edit("top")
	def __set_top(self, v) :
		self.__top = v - ((self.__height - self.__width) / 2 if self.orientation[2] % 180 else 0)


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


	def get_terms_flat(self) :
		for t in self.terms :
			if t.variadic :
				for nr, index in sorted(self.get_indexed_terms(t), key=lambda x: x[1]) :
					yield t, nr
			else :
				yield t, None


	def stringified_value(self, value) :
		assert(value is None or isinstance(value, tuple))
		v = value if value else ("None", )
		return ",".join(str(s) for s in v)


	def get_presentation_text(self) :
		cls = core.get_proto_name(self.prototype)
		if cls in self.__lbl_fmt :
			newtxt = self.__lbl_fmt[cls].format(self.stringified_value(self.value))
		else :
			newtxt = self.caption
		if 0 :
			newtxt = newtxt + ":" + str(self.get_instance_id())
		return newtxt


	def __init_label_fmt_table(self) :
#TODO globalize
		self.__lbl_fmt = {
			core.get_proto_name(core.ConstProto()) : "{0}",
			core.get_proto_name(core.DelayProto()) : "Delay({0})",
			core.get_proto_name(core.TapProto()) : "Tap({0})",
			core.get_proto_name(core.TapEndProto()) : "TapEnd({0})",
			core.get_proto_name(core.InputProto()) : "Input({0})",
			core.get_proto_name(core.OutputProto()) : "Output({0})",
			core.get_proto_name(core.VariadicInProto()) : "VariadicIn({0})",
			core.get_proto_name(core.VariadicOutProto()) : "VariadicOut({0})",
			core.get_proto_name(core.JointProto()) : "",
			core.get_proto_name(core.PipeProto()) : "Pipe({0})",
			core.get_proto_name(core.PipeEndProto()) : "PipeEnd({0})",
			core.get_proto_name(core.TextAreaProto()) : "{0}",
			core.get_proto_name(core.BufferProto()) : "Buffer({0})",
#			"ConstInputProto":"ConstInput({0})",
		}


	presentation_text = property(get_presentation_text)


	def get_term_presentation_text(self, t, nr) :
		term_label = t.name
		if core.compare_proto_to_type(self.prototype, core.ConstProto) :
			term_label = ""#str(self.model.value)
		if t.variadic : #XXX nr != None
			term_label += str(self.get_term_index(t, nr))
		return term_label


	def __init__(self, prototype, model, instance_id=None, left = 0, top = 0) :
		"""
		when there is no parent use for model argument value
		'itentionally left blank' instead of GraphModel instance
		"""

		super(BlockModel, self).__init__(prototype, model)

		self.__instance_id = instance_id
		self.__orientation = (0, 0, 0)
		self.__caption = prototype.type_name
		self.__left = left
		self.__top = top
		self.__width, self.__height = prototype.default_size
		self.__model = model
		self.__can_move = True
		self.__value = tuple(dv for name, dv in prototype.values) if prototype.values else None
		self.__term_meta = { t.name: { "multiplicity" : 1, (0, "index") : 0 } for t in prototype.terms if t.variadic }


		self.__init_label_fmt_table()


	def __repr__(self) :
		return "%s(%s)" % (self.prototype.type_name, str(self.value))


# ------------------------------------------------------------------------------------------------------------

class GraphModel(object) :


	def remove_listener(self, listener) :
		self.__listeners.remove(listener)


	def add_listener(self, listener) :
		self.__listeners.append(listener)


	def get_meta(self) :
		return self.__meta


	def set_meta(self, key, value, remove_key=False) :
		key_present, old_value = False, None
		if key in self.__meta :
			key_present, old_value = True, self.__meta[key]
		self.__meta[key] = value
		self.__history_frame_append("sheet_meta_changed", (key, old_value, key_present))
		self.__on_meta_changed(key, key_present, old_value, value)


#	def set_block_meta(self, block, meta) :
#		for k, v in meta.iteritems() :
#			self.__getattribute__("_BlockModel__set_"+k)(v)


	def add_block(self, block, reassign_id_if_needed=True) :

		block_id = block.get_instance_id()

		if block_id is None or block_id in self.__block_ids :
			block_id = max(self.__block_ids.keys()) + 1 if self.__block_ids else 0
			block.set_instance_id(block_id)

		assert(not(block_id in self.__block_ids))

		self.__block_ids[block.get_instance_id()] = block

		self.blocks.append(block)
#		block.graph = self #XXX ?
		self.__history_frame_append("block_added", (block, ))
		self.__on_block_added(block)


	def remove_block(self, block) :
		self.blocks.remove(block)

		instance = self.__block_ids.pop(block.get_instance_id())
		assert(instance == block)

		succs = [ c for c in self.connections.iteritems() if c[0][0] == block ]

		for s, dests in succs :
			for d in dests :
				self.remove_connection(*(s+d))

		preds = [ c for c in self.connections.iteritems()
			if reduce(lambda a, dest: a or dest[0] == block, c[1], False) ]

		for s, dests in preds :
			for d in [ dest for dest in dests if dest[0] == block ] :
				self.remove_connection(*(s+d))

		self.__history_frame_append("block_removed", (block, ))
		self.__on_block_removed(block)


	def can_connect(self, sb, st, tb, tt) :
#		print "can_connect:", sb, st, tb, tt
#TODO if variadic check max count
		st, sn = st if isinstance(st, tuple) else (st, 0)
		tt, tn = tt if isinstance(tt, tuple) else (tt, 0)
		return (st.direction != tt.direction and
			st.direction in (core.INPUT_TERM, core.OUTPUT_TERM) and
			tt.direction in (core.INPUT_TERM, core.OUTPUT_TERM))


	def set_connection_meta(self, b0, t0, b1, t1, meta) :
		old_meta = self.__connections_meta[(b0, t0, b1, t1)]
#		print(here(3), "old:", old_meta)
		if (b0, t0, b1, t1) in self.__connections_meta :
			self.__connections_meta[(b0, t0, b1, t1)] = meta
		else :
			self.__connections_meta[(b0, t0, b1, t1)].update(meta)
#		print(here(3), "new:", meta)
		self.__history_frame_append("connection_meta", (b0, t0, b1, t1, old_meta))
		self.__on_connection_changed(b0, t0, b1, t1)


	def get_connection_meta(self, b0, t0, b1, t1) :
#		print(here(3), "new:", self.__connections_meta)
		return dict(self.__connections_meta[(b0, t0, b1, t1)])


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


	def add_connection(self, b0, t0, b1, t1, meta, deserializing=False) :
#		print here(), b0, t0, b1, t1
		if not deserializing :

			if not self.can_connect(b0, t0, b1, t1) :#TODO add multiplicity
				raise Exception("can't connect")
#			print here(), b0, t0, b1, t1
			b0, t0, b1, t1 = (b0, t0, b1, t1) if t0.direction == core.OUTPUT_TERM else (b1, t1, b0, t0)
			if not isinstance(t0, tuple) and t0.variadic :
				m0, t0 = self.__add_variadic_term(b0, t0, deserializing=deserializing)
			if not isinstance(t1, tuple) and t1.variadic :
				m1, t1 = self.__add_variadic_term(b1, t1, deserializing=deserializing)

		if (b0, t0) in self.__connections :
			self.__connections[(b0, t0)].append((b1, t1))
		else :
			self.__connections[(b0, t0)] = [(b1, t1)]
		self.__connections_meta[(b0, t0, b1, t1)] = meta

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


	# ---------------------------------------------------------------------------------

	def __on_block_added(self, block) :
		for listener in self.__listeners :
			listener.block_added(self, block)

	def __on_block_removed(self, block) :
		for listener in self.__listeners :
			listener.block_removed(self, block)

	def __on_block_changed(self, block, event, old_meta, new_meta) :
		assert(not(old_meta is None))
		self.__history_frame_append("block_meta", (block, old_meta))
		for listener in self.__listeners :
			listener.block_changed(self, block, event)

	def __on_connection_added(self, sb, st, tb, tt, deserializing=False) :
		for listener in self.__listeners :
			listener.connection_added(self, sb, st, tb, tt, deserializing)

	def __on_connection_removed(self, sb, st, tb, tt) :
		for listener in self.__listeners :
			listener.connection_removed(self, sb, st, tb, tt)

	def __on_connection_changed(self, sb, st, tb, tt) :
#		raise Exception("not implemented")
		for listener in self.__listeners :
			listener.connection_changed(self, sb, st, tb, tt)
#			print(here(), (sb, st, tb, tt))

	def __on_meta_changed(self, key, key_present, old_value, new_value) :
		for listener in self.__listeners :
			listener.meta_changed(self, key, key_present, old_value, new_value)

	# ---------------------------------------------------------------------------------

	def undo(self) :
		if self.__undo_stack :
			assert(self.__history_frame_depth == 0)
#			print(here(), len(self.__undo_stack), len(self.__redo_stack))
			frame = self.__undo_stack.pop()
			undo_stack = self.__undo_stack
			self.__undo_stack = self.__redo_stack
			self.begin_edit()
			self.__revert_frame(frame)
			self.end_edit()
			self.__undo_stack = undo_stack
			assert(self.__history_frame_depth == 0)
#			print(here(), len(self.__undo_stack), len(self.__redo_stack))


	def redo(self) :
		if self.__redo_stack :
			assert(self.__history_frame_depth == 0)
			frame = self.__redo_stack.pop()
			self.begin_edit()
			self.__revert_frame(frame)
			self.end_edit()
			assert(self.__history_frame_depth == 0)
#			print(here(), len(self.__undo_stack), len(self.__redo_stack))


	inverse_actions = {
		"connection_added" : lambda self, data: self.remove_connection(*data[0]),
		"connection_removed" : lambda self, data: self.add_connection(*data[0], meta=data[1]),
		"connection_meta" : lambda self, data: self.set_connection_meta(*data),
		"block_removed" : lambda self, data: self.add_block(data[0]),
		"block_added" : lambda self, data: self.remove_block(data[0]),
		"block_meta" : lambda self, data: data[0].set_meta(data[1]),
		"sheet_meta_changed" : lambda self, data: self.set_meta(data[0], data[1], remove_key=not data[2]),
	}


	def __revert_frame(self, frame) :
		self.__redoing = True
		for act, data in frame :
			GraphModel.inverse_actions[act](self, data)
		self.__redoing = False

	#XXX do i really want to have logic of history logging in _this_ class?!
	def __history_frame_append(self, action, data) :
		assert(action in GraphModel.inverse_actions)
		if not self.__enable_logging :
			return None
		if not self.__redoing :
			del self.__redo_stack[:]
		assert(not(data is None))
		self.__assert_editing()
		if self.__history_frame == None:#XXX should not happen because of __assert_editing
			raise Exception("no opened frame!")
		else :
			self.__history_frame.insert(0, (action, data))


	def begin_edit(self) :
		if not self.__enable_logging :
			return None
		self.__editing = True
		if self.__history_frame_depth == 0 :
			self.__history_frame = []
		self.__history_frame_depth += 1


	def end_edit(self) :
		self.__history_frame_depth -= 1
		if self.__history_frame_depth < 0 :
			raise Exception("undo framing underflow!")
		if self.__history_frame_depth == 0:
			if self.__history_frame :
#				print(here(), len(self.__history_frame), len(self.__undo_stack), len(self.__redo_stack))
				self.__undo_stack.append(self.__history_frame)
#				print(here(), len(self.__undo_stack), len(self.__redo_stack))
			self.__history_frame = None
			self.__editing = False


	def __assert_editing(self) :
		if self.__enable_logging and not self.__editing :
			raise Exception("not editing")


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
		for k, v in self.__meta.items() :
			self.__on_meta_changed(k, True, None, v)


	blocks = property(lambda self: self.__blocks)

	connections = property(lambda self: self.__connections)

#	listeners = property(lambda self: self.__listeners)

	connections_meta = property(lambda self: self.__connections_meta)

#	name = property(lambda self: "Sheet#1")#TODO

	def __init__(self) :

		self.__history_frame_depth = 0 #XXX equals bool(self.__editing)
		self.__history_frame = None
		self.__undo_stack = []
		self.__redo_stack = []
		self.__editing = False
		self.__enable_logging = True
		self.__redoing = False

		self.__blocks = []
		self.__connections = {}
		self.__listeners = []
		self.__connections_meta = {}
		self.__meta = {}
		self.__block_ids = {}

# ------------------------------------------------------------------------------------------------------------

MAX_WORKERS = 1
WORKBENCH_EXTENSION = ("bloced workbench", "*.w")
KNOWN_EXTENSIONS = ( WORKBENCH_EXTENSION, ("all files", "*") )
IMPORT_EXTENSIONS = ( ("bloced sheet", "*.bloc"), ("all files", "*") )

#def synchronized(lock):
#	def wrap(f):
#		def newFunction(*args, **kw):
#			lock.acquire()
#			try:
#				return f(*args, **kw)
#			finally:
#			lock.release()
#		return newFunction
#	return wrap

#def sync() :
#	def wrapper(f) :
#		a[0].lock.acquire()
#		def wrap(*a, **b) :
#			return f(*a, **b)
#		a[0].lock.release()
#	return wrapper

def sync(f) :
	def wrap(*a, **b) :
		a[0].lock.acquire()
		ret = f(*a, **b)
		a[0].lock.release()
		return ret
	return wrap


def catch_all(f) :
	def wrap(*a, **b) :
		try :
			ret = f(*a, **b)
		except Exception as e :
			print(here(10), e)
			os._exit(1)
		else :
			return ret
	return wrap


class WorkbenchData(object) :


	sheets = property(lambda self: self.__sheets)


	def get_meta(self) :
		prefix = "_" + self.__class__.__name__
		m = { k : self.__dict__[(prefix+k) if k.startswith("__") else k] for k in self.PERSISTENT }
		return m


	meta = property(get_meta)


#	def get_sheet_by_name(self, name) :
#		return [ (s, i) for s, i in zip(self.__sheets, count()) if s.name == name ]


	def is_valid_name(self, a) :
		first = set("@_abcdefghijklmnopqrstuvwxyz")	
		other = first.union(":012345679")
		s = a.lower()
		return s and s[0] in first and all([ c in other for c in s ])


	def get_free_sheet_name(self, seed="Sheet{0}", check_validity=True) :
		"""
		returns free sheet name
		seed is format string with at least one placeholder
		"""
		i = 1
		name = seed.format(i)
		if check_validity and not self.is_valid_name(name) :
			return None
		while name in self.__sheets :
			name = seed.format(i)
			i += 1
		return name


	def __init__(self, lib_dir=None,
			do_create_block_factory=True,
			blockfactory=None) :

		self.PERSISTENT = ( "__port", "__board", "__gateway_enabled" )

		self.blockfactory = blockfactory
		if do_create_block_factory :
			self.blockfactory = core.create_block_factory(
				scan_dir=lib_dir)

		self.lock = Lock()

		self.__sheets = {}
		self.__meta = {}


class Workbench(WorkbenchData, GraphModelListener) :


	@sync
	def rename_sheet(self, name=None, new_name=None) :
		sheet, name = self.delete_sheet(name=name)
		self.add_sheet(sheet=sheet, name=new_name)


	def clear(self) :
		for name in list(self.sheets.keys()) :
			self.delete_sheet(name=name)
		self.clear_meta()


	def add_sheet(self, sheet=None, name=None) :
#TODO raise event
		if not self.is_valid_name(name) :
			raise Exception("invalid_resource_name")
		if name in self.sheets :
			raise Exception("resource_name_allready_used")
		if sheet is None :
			sheet = GraphModel()
#		print here(), name, sheet
		self.sheets[name] = sheet
		sheet.add_listener(self)
		self.__changed("sheet_added", (sheet, name))


	def delete_sheet(self, name=None) :
#		if name != None :
#			sheet, = self.get_sheet_by_name(name)
		sheet = self.sheets.pop(name)
		sheet.remove_listener(self)
		self.__changed("sheet_deleted", (sheet, name))
		return (sheet, name)


	def set_meta(self, m) :
		prefix = "_" + self.__class__.__name__
		self.__dict__.update({ (prefix+k) if k.startswith("__") else k : v for k, v in m.items() })
#XXX		self.__changed("meta_changed", self.get_meta())


	def clear_meta(self) :
		prefix = "_" + self.__class__.__name__
		self.__dict__.update({ (prefix+k) if k.startswith("__") else k : None for k in self.PERSISTENT })
		self.__changed("meta_changed", self.get_meta())


	def build(self) :
		try :
			board_type = self.get_board()
			sheets = self.sheets
			meta = self.get_meta()
#XXX XXX XXX clone data before passing to job queue!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
			self.__jobs.put(("build", (board_type, sheets, meta)))

#			self.build_job(board_type, sheets, meta)#TODO refac build invocation

		except Exception as e :
			print(here(), traceback.format_exc())
			self.__messages.put(("status", (("build", False, "compilation_failed"), {}))) #TODO say why


	class TermStream(object) :

		def write(self, s) :
			msg_info = {}
			msg_info["term_stream"] = s
			self.__messages.put(("status", (("build", None, "compilation_progress"), msg_info)))

		def __init__(self, __messages) :
			self.__messages = __messages


	def build_job(self, board_type, sheets, meta) :

		if board_type is None :
			self.__messages.put(("status", (("build", False, "board_type_not_set"), {})))
			return None

		board_info = build.get_board_types()[board_type]
		variant = board_info["build.variant"] if "build.variant" in board_info else "standard" 

		self.__messages.put(("status", (("build", True, "build_started"), {})))

		w_data = serializer.get_workbench_data(self)#TODO refac build invocation

		out_fobj = StringIO()
		try :
			w = Workbench(passive=True, do_create_block_factory=False,
				blockfactory=self.blockfactory)
			local_lib = core.BasicBlocksFactory(load_basic_blocks=False)
			local_lib.load_standalone_workbench_lib(None, "<local>",
				library=w.blockfactory,
				w_data=w_data)
			library = core.SuperLibrary([w.blockfactory, local_lib])
			serializer.restore_workbench(w_data, w,
				use_cached_proto=False,
				library=library)
			libs_used, = implement.implement_workbench(w, w.sheets, w.get_meta(),
				ccodegen, core.KNOWN_TYPES, library, out_fobj)
		except Exception as e:
			print(here(), traceback.format_exc())
			self.__messages.put(("status", (("build", False, str(e)), {})))
			return None

		if out_fobj.tell() < 1 :
			self.__messages.put(("status", (("build", False, "no_code_generated"), {})))
			return None

		source = out_fobj.getvalue()
		print(source)

		all_in_one_arduino_dir = self.config.get("Path", "all_in_one_arduino_dir")
		if not all_in_one_arduino_dir :
			all_in_one_arduino_dir = None
		libc_dir, tools_dir, boards_txt, target_files_dir = build.get_avr_arduino_paths(
			all_in_one_arduino_dir=all_in_one_arduino_dir)

		source_dirs = set()
		for l in library.libs :
			if l.name in libs_used :
				for src_file in l.source_files :
					source_dirs.add(os.path.dirname(src_file))

		install_path = os.getcwd()#XXX replace os.getcwd() with path to dir with executable file
		blob_stream = StringIO()

#		term_stream = StringIO()
#		term_stream = sys.stdout
		term_stream = Workbench.TermStream(self.__messages)

		defines = {}

		if self.__gateway_enabled :
			defines["DBG_ENABLE_GATEWAY"] = 1

		try :
#TODO implement in chain.py
			rc, = build.build_source(board_type, source,
				aux_src_dirs=(
					(os.path.join(target_files_dir, "cores", "arduino"), False),
					(os.path.join(target_files_dir, "variants", variant), False),
	#				(os.path.join(install_path, "library", "arduino"), False),
				) + tuple( (path, True) for path in source_dirs ),#TODO derive from libraries used
				aux_idirs=[ os.path.join(install_path, "target", "arduino", "include") ],
				boards_txt=boards_txt,
				libc_dir=libc_dir,
	#			board_db={},
				ignore_file=None,#"amkignore",
	#			ignore_lines=( "*.cpp", "*.hpp", "*" + os.path.sep + "main.cpp", ), #TODO remove this filter with adding cpp support to build.py
				ignore_lines=( "*" + os.path.sep + "main.cpp", ),
	#			prog_port=None,
	#			prog_driver="avrdude", # or "dfu-programmer"
	#			prog_adapter="arduino", #None for dfu-programmer
				optimization="-Os",
				defines=defines,
				verbose=False,
				skip_programming=True,#False,
	#			dry_run=False,
				blob_stream=blob_stream,
				term=term_stream)
		except Exception as e :
			self.__messages.put(("status", (("build", False, "compilation_failed"), {"term_stream":str(e)})))
			return None

		msg_info = {}
#		if term_stream != sys.stdout :
#			msg_info["term_stream"] = term_stream

		if rc :
			self.__blob = blob_stream.getvalue()
			self.__blob_time = time.time()
		else :
			self.__messages.put(("status", (("build", False, "compilation_failed"), msg_info)))
			return None
#			return (False, "build_failed")

		self.__messages.put(("status", (("build", True, ""), msg_info)))
#		return (True, "ok")
#		return (True, (blob, ))


#	def upload(board_type, prog_port, blob) :
	def upload(self) :
#		prog_port, blob = None, None
		board_info = self.__board_types[self.get_board()]
		prog_mcu = board_info["build.mcu"]
#TODO acquire blob after job is taken from queue, so that freshly build blob is used
		self.__jobs.put(("upload", (prog_mcu, self.get_port(), self.__blob, self.__blob_time)))


	def upload_job(self, prog_mcu, port, blob, blob_time) :
		if blob is None :
			self.__messages.put(("status", (("upload", False, "upload_failed"),
				{ "other" : { "reason" : "no_blob"}})))
			return None

		if self.__gateway_enabled :
			self.__gateway.detach()

		self.__messages.put(("status", (("upload", True, "upload_started"),
			{ "other" : { "info" : (blob_time, prog_mcu, port) }})))

		#TODO implement in chain.py
		rc = build.program("avrdude", port, "arduino", prog_mcu, None,
			a_hex_blob=blob,
			verbose=False,
			dry_run=False)

		if rc[0] :
#			print("programming failed ({})".format(rc[0]))
			self.__messages.put(("status", (("upload", False, "upload_failed"),
				{ "other" : { "reason" : rc[0] }})))
		else :
#			print("programming succeeded")
			self.__messages.put(("status", (("upload", True, "upload_done"), {})))

		if self.__gateway_enabled :
			self.__gateway.attach()


	state_info = property(lambda self: self.get_state_info())


	def get_state_info(self) :
		return ("", "")#left, right


	@sync
	def __get_should_finish(self) :
		return self.__should_finish


	@sync
	def __set_should_finish(self) :
		self.__should_finish = True


	def __poll_gateway(self) :
		if self.__gateway.poll_events() :
			print(here())
			self.__messages.put(("status", (("gateway", True, "status"),
				{ "other" : None})))


	@catch_all
	def __timer_thread(self) :
#		port_check = time.time()
		while not self.__get_should_finish() :

			tm = time.time()

			if self.__gateway_enabled and not self.__gateway is None : #TODO make __gateway_enabled reflect existance of instance
				self.__poll_gateway()

			jobs = []
			try :
				while not self.__jobs.empty() :
					jobs.append(self.__jobs.get_nowait())
			except QueueEmpty :
				pass

#			print here(), jobs

			for job_type, job_args in jobs :
				if job_type == "build" :
					print(here())
					board_type, sheets, meta = job_args
					self.build_job(board_type, sheets, meta)#TODO try..except
				if job_type == "upload" :
					print(here())
					self.upload_job(*job_args)
#TODO put to message to signal job done

			if time.time() - tm < 0.3 :
				time.sleep(0.3)
#TODO TODO TODO		self.__timer_job()
			now = time.time()

#			if now - port_check >= self.__port_check_time :
##				print ("check ports")
#				self.rescan_ports()
#				port_check = time.time()


	#sync
	def rescan_ports(self) :
		self.set_port_list(build.get_ports())


	def __timer_job(self) :
#TODO TODO TODO
		pass


	def read_messages(self) :
		messages = []
		try :
			while not self.__messages.empty() :
				messages.append(self.__messages.get_nowait())
				print(here(), messages[-1])
		except QueueEmpty :
			pass
		return messages


	def fire_callbacks(self) :
		if not Workbench.MULTITHREADED :
			self.__timer_job()
		for msg, (aps, akw) in self.read_messages() :
			if msg in self.__callbacks :
				callback = self.__callbacks[msg]
				if callback :
					callback(*aps, **akw)

	@sync
	def get_port_list(self) :
		return self.__ports


	@sync
	def set_port_list(self, port_list) :
		if self.__ports != port_list :
			self.__ports = port_list
			self.__messages.put(("ports", ([], {})))
#			self.__messages.put(("status", ([("ports rescanned", ":-)")], {})))


	def get_board_types(self) :
		return self.__board_types


	@sync
	def set_board(self, board) :
		if board in self.__board_types :
			self.__board = board
			self.__changed("board_set", (board, ))
		return self.__board


#	@sync
	def get_board(self) :
		return self.__board


	@sync
	def set_port(self, port) :
		if port in { p[0] for p in self.__ports } :
			self.__port = port
			if self.__gateway_enabled :
				self.__gateway.attach_to(self.__port)#TODO gateway port could differ from programming port
			self.__changed("port_set", (port, ))
		return self.__port


#	@sync
	def get_port(self) :
		return self.__port


	def set_gateway_enabled(self, en) :
		start_gw = bool(en) and bool(self.__gateway_enabled) != bool(en)
		stop_gw = (not bool(en)) and bool(self.__gateway_enabled) != bool(en)
		self.__gateway_enabled = en
		if start_gw :
			assert(self.__gateway is None)
			print(here())
			self.__gateway = gateway.Gateway()
			self.__gateway.configure_user_port("VSP_AUTO", None, None)
			self.__gateway.attach_to(self.__port)
		elif stop_gw :
			assert(not self.__gateway is None)
			print(here())
			self.__gateway.destroy()
			self.__gateway = None
		self.__changed("gateway_enable_changed", (en, )) #TODO implement handler


	def get_gateway_enabled(self) :
		return bool(self.__gateway_enabled)


	def get_gw_outer_port(self) :
		if self.__gateway_enabled :
			return self.__gateway.get_user_port()
		return None


	def get_gw_board_port_ready(self) :
		if self.__gateway_enabled :
			return self.__gateway.get_board_port_ready()
		return False


	def __changed(self, event, data) :
		if self.__change_callback :
			self.__change_callback(self, event, data)


	@sync
	def have_blob(self) :
		return not self.__blob is None


	@sync
	def blob_time(self) :
		return self.__blob_time


	def __sheet_changed(self, sheet) :
		self.__changed("sheet_modified", (sheet, ))


	def block_added(self, sheet, block) :
		self.__sheet_changed(sheet)

	def block_removed(self, sheet, block) :
		self.__sheet_changed(sheet)

	def block_changed(self, sheet, block, event=None) :
		self.__sheet_changed(sheet)

	def connection_added(self, sheet, sb, st, tb, tt, deserializing=False) :
		self.__sheet_changed(sheet)

	def connection_removed(self, sheet, sb, st, tb, tt) :
		self.__sheet_changed(sheet)

	def connection_changed(self, sheet, sb, st, tb, tt) :
		self.__sheet_changed(sheet)

	def meta_changed(self, sheet, key, key_present, old_value, new_value) :
		self.__sheet_changed(sheet)


	MULTITHREADED = True


#	@catch_all
	def __init__(self, lib_dir=None,
			passive=True,
			config=None,
			status_callback=None,
			ports_callback=None,
			monitor_callback=None,
			change_callback=None,
			do_create_block_factory=True,
			blockfactory=None) :

		"""
		default value for ALL meta is None, stick with it
		"""

		super(Workbench, self).__init__(lib_dir=lib_dir,
			do_create_block_factory=do_create_block_factory,
			blockfactory=blockfactory)


		self.config = config
		if config :
			all_in_one_arduino_dir = self.config.get("Path", "all_in_one_arduino_dir")
			if not all_in_one_arduino_dir :
				all_in_one_arduino_dir = None
		else :
			all_in_one_arduino_dir = None

		self.__board = None
		self.__port = None
		self.__board_types = build.get_board_types(all_in_one_arduino_dir=all_in_one_arduino_dir)
		self.__gateway_enabled = False
		self.__gateway = None

		self.__blob = None
		self.__blob_time = None

		self.__callbacks = {}
		self.__callbacks["status"] = status_callback
		self.__callbacks["ports"] = ports_callback
		self.__callbacks["monitor"] = monitor_callback

		self.__change_callback = change_callback

		self.__port_check_time = 1.0

		self.__ports = []

		self.__should_finish = False
		self.__messages = Queue()
		self.__jobs = Queue()
#XXX
		if not passive :
			self.set_port_list(build.get_ports())

		if passive or not Workbench.MULTITHREADED :
			print("running single-threaded!!!")
		else :
			self.tmr = Thread(target=self.__timer_thread)
			self.tmr.start()


	def finish(self) :
		if not self.__gateway is None :
			self.__gateway.destroy()
			self.__gateway = None
		self.__set_should_finish()
		if Workbench.MULTITHREADED :
			self.tmr.join()

# ------------------------------------------------------------------------------------------------------------


