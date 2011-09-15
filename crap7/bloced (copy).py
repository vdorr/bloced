
from Tkinter import * #TODO this is not good
import tkFont
from pprint import pprint
from collections import namedtuple
import autoroute
from tkFileDialog import askopenfilename, asksaveasfilename
from sys import exit
from dfs import *
from functools import partial
from itertools import ifilter, imap, chain, dropwhile, groupby
from serializer import *
from implementer import implement_dfs
#import argparse #TODO use sys instead
import traceback
import pyperclip
import mathutils
import os
import string
import undo
import tkMessageBox
import pickle

# ------------------------------------------------------------------------------------------------------------

#TODO map from model to presentation: { dfs.JointProto : Joint, BlockModel:
#TODO somehow implement system of "actions" so its not neccessary to have separate  implmentations
# for menu and shortcut handlers, use functools.partial or so, look at gtk

# ------------------------------------------------------------------------------------------------------------

BIT_SHIFT = 0x001
BIT_CAPSLOCK = 0x002
BIT_CONTROL = 0x004
BIT_LEFT_ALT = 0x008
BIT_NUMLOCK = 0x010
BIT_RIGHT_ALT = 0x080
BIT_MB_1 = 0x100
BIT_MB_2 = 0x200
BIT_MB_3 = 0x400

# ------------------------------------------------------------------------------------------------------------

class Configuration(object):
	GRID_SIZE = 4
	CANVAS_WIDTH = 2048
	CANVAS_HEIGHT = 2048
	BLOCK_WIRE_STUB = 16
	SELECTION_RECT_SIZE = 2
	APP_NAME = "bloced"
	NONE_FILE = "<unsaved file>"
	SAVE_BEFORE_CLOSE = "Save changes before closing?"

cfg = Configuration()

# ------------------------------------------------------------------------------------------------------------

selection_t = namedtuple("snt", [ "blocks", "lines" ])#, "joints" ]);
event_t = namedtuple("event_t", ["x", "y", "state"])

# ------------------------------------------------------------------------------------------------------------

class textbox(Frame):

	def __init__(self,parent, msg):
		Frame.__init__(self,parent)
		self.g_label = Label(self,text=msg)
		self.g_label.pack(side=LEFT,expand=False)
		self.g_entry = Entry(self)
		self.g_entry.pack(side=LEFT, fill=X, expand=True)
		self.pack(fill=X, anchor=NW, expand=True)

	def text(self):
		return self.gui["entry"].get()

# ------------------------------------------------------------------------------------------------------------

class Block(Canvas) :

	def onMouseDown(self, e) :
		return self.editor.blckMouseDown(self, e)

	def onMouseMove(self, e) :
		return self.editor.blckMouseMove(self, e)

	def onMouseUp(self, e) :
		return self.editor.blckMouseUp(self, e)

	#TODO class EditableBlock(Block) :
	def onDblClick(self, e) :
		if type(self.model.prototype) in (ConstProto, DelayProto) :
			entry = Entry(self)
			entry.insert(0, str(self.model.value))
			w = self.create_window(0, 0, window=entry, anchor=NW)
			entry.bind("<Return>", lambda e: self.close_editor(True, w, entry))
			entry.bind("<Escape>", lambda e: self.close_editor(False, w, entry))
			entry.pack(side=LEFT, fill=X)
			entry.focus()

	def close_editor(self, accept, w, entry) :
		if accept :
			self.model.value = str(entry.get())
			self.update_text()
		self.delete(w)
		entry.destroy()
		self.config(width=self.model.width, height=self.model.height, bg="white",
			borderwidth=0, highlightthickness=0)

	def update_text(self) :
		if type(self.model.prototype) == ConstProto :
			newtxt = self.model.value
		elif type(self.model.prototype) == DelayProto :
			newtxt = "Delay (" + self.model.value + ")"
		else :
			newtxt=self.model.caption
		self.itemconfigure(self.caption_txt, text=newtxt)

	def get_term_poly(self, tx, ty, tsz, side, direction) :
		orgx, orgy = tx+0.5*tsz, ty+0.5*tsz
		ang = { N : 90, S : 270, W : 0, E : 180, C : 0, }
		a = (ang[side] + (0 if direction == INPUT_TERM else 180)) % 360
		sin_angle, cos_angle = mathutils.rotate4_trig_tab[a]
		r = lambda xx, yy: (
			orgx + ((xx - orgx) * cos_angle - (yy - orgy) * sin_angle),
			orgy + ((xx - orgx) * sin_angle + (yy - orgy) * cos_angle))
		return r(tx, ty) + r(tx+tsz, ty+tsz/2) + r(tx, ty+tsz)

	def __init__(self, editor, model) :
		self.editor = editor
		self.canvas = editor.canv
		self.model = model

		Canvas.__init__(self, self.editor.canv,
			width=self.model.width, height=self.model.height,
			bg="white", borderwidth=0, highlightthickness=0)

		self.window = self.canvas.create_window(self.model.left, self.model.top,
			window=self, anchor=NW)
		
		self.bind("<B1-Motion>", self.onMouseMoveW)
		self.bind("<ButtonPress-1>", self.onMouseDownW)
		self.bind("<ButtonRelease-1>", self.onMouseUpW)
		self.bind("<Configure>", self.onConfigure)
		self.bind("<Double-Button-1>", self.onDblClick)

		self.border_rect = self.create_rectangle(0, 0, self.model.width - 1, self.model.height - 1)
		self.caption_txt = self.create_text(0, 0, anchor=NW)
		self.update_text()
		
		self.movingObject = None
		self.affected_wires = None
		self.window2term = {}
		self.__term2txt = {}

		for t in self.model.terms :
			o = self.create_polygon(0, 0, fill="white", outline="black", tags=t.name)
			self.bind_as_term(o)
			txt = self.create_text(0, 0, text=t.name, anchor=NW, fill="black")
			self.window2term[o] = t
			self.__term2txt[t] = txt
		self.reshape()

	def reshape(self) :
		self.coords(self.border_rect, 0, 0, self.model.width-1, self.model.height-1)
		self.canvas.coords(self.window, self.model.left, self.model.top)
		self.canvas.itemconfig(self.window, width=self.model.width, height=self.model.height)

		tsz = 8#TODO precompute
		sides = {
			N : lambda p: (self.model.width*p-tsz/2, 0, 0, tsz),
			S : lambda p: (self.model.width*p-tsz/2, self.model.height-tsz, 0, -tsz),
			W : lambda p: (0, self.model.height*p-tsz/2, tsz, 0),
			E : lambda p: (self.model.width-tsz-1, self.model.height*p-tsz/2, -tsz, 0),
			C : lambda p: (0.5*self.model.width, 0.5*self.model.height, 0, 0),
		}
		fnt = tkFont.Font()
		txt_height = fnt.metrics("linespace")
		for w, t  in self.window2term.iteritems() :
			x, y, txtx, txty = sides[t.get_side(self.model)](t.get_pos(self.model))
			self.coords(w, *self.get_term_poly(x, y, tsz, t.get_side(self.model), t.direction))
			self.coords(self.__term2txt[t], x+txtx, y-(0.2*txt_height)+txty)

	#TODO move to superclass?
	def bind_as_term(self, o) :
		self.tag_bind(o, "<B1-Motion>", self.onMouseMove)#TODO use partial(
		self.tag_bind(o, "<ButtonPress-1>", self.onMouseDown)
		self.tag_bind(o, "<ButtonRelease-1>", self.onMouseUp)

	#TODO move to superclass?
	def get_wires(self, sel_blocks=None) :
		sel_blocks = sel_blocks if sel_blocks else (self, )
		return filter(lambda c:
			reduce(lambda x, blck: x or (blck.model in (c[0][0], c[0][2])), sel_blocks, False),
			self.editor.connection2line.items())

	def onMouseDownW(self, e) :
		self.move_start = (e.x_root, e.y_root)
#		if e.state & BIT_SHIFT : #TODO
#			pass
		if self.editor.selection :
			sel_blocks = tuple(self.editor.selection.blocks)
		else :
			sel_blocks = (self, )
		self.affected_wires = self.get_wires(sel_blocks=sel_blocks)

	def onMouseMoveW(self, e) :
#		if not self.movingObject and self.start : # TODO move to editor
		if not self.movingObject and self.move_start : # TODO move to editor
			self.editor.move_selection(e.x_root-self.move_start[0], e.y_root-self.move_start[1])
			self.move_start = (e.x_root, e.y_root)

	def onMouseUpW(self, e) :
		self.move_start = None
		if self.affected_wires :
			for k, v in self.affected_wires :
				self.editor.update_connection(*(k + (True,)))
		self.affected_wires = None

	def onConfigure(self, e) :
		pass

# ------------------------------------------------------------------------------------------------------------

class Joint(object) :

	def __init__(self, editor, model) :
		self.editor = editor
		self.canvas = editor.canv
		self.model = model
		self.window = self.canvas.create_oval(self.model.left, self.model.top,
			self.model.width+self.model.left, self.model.height+self.model.top,
			fill="black")
		self.editor.canv.tag_bind(self.window, "<B1-Motion>", self.onMouseMoveW)
		self.editor.canv.tag_bind(self.window, "<ButtonPress-1>", self.onMouseDownW)
		self.editor.canv.tag_bind(self.window, "<ButtonRelease-1>", self.onMouseUpW)
		self.movingObject = None

	def reshape(self) :
		self.canvas.coords(self.window, self.model.left, self.model.top,
			self.model.width+self.model.left, self.model.height+self.model.top)

	def get_wires(self, sel_blocks=None) :
		sel_blocks = sel_blocks if sel_blocks else (self, )
		return filter(lambda c:
			reduce(lambda x, blck: x or (blck.model in (c[0][0], c[0][2])), sel_blocks, False),
			self.editor.connection2line.items())

	def onMouseDownW(self, e) :
		if self.editor.manipulating :
			return None
		self.editor.manipulating = "joint"
		self.start = e
		self.affected_wires = filter(lambda c: self.model in (c[0][0], c[0][2]), #sb, st, tb, tt
			self.editor.connection2line.items())
		for k, v in self.affected_wires :
			self.editor.update_connection(*(k + (False,)))

#	def onMouseMoveW(self, e, nocheck=False) :
#		if nocheck or (not self.movingObject and self.editor.manipulating == "joint") :
#			diffX, diffY = (e.x - self.start.x), (e.y - self.start.y)
#			self.canvas.move(self.window, diffX, diffY)
#			self.start = e
#			self.model.left, self.model.top, r, b = tuple(self.canvas.bbox(self.window))
#			for k, v in self.affected_wires :
#				self.editor.update_connection(*(k + (False,)))

	def onMouseMoveW(self, e) :
		if not self.movingObject and self.editor.manipulating == "joint" :
			self.move(e, self.start)
			self.start = e
			for k, v in self.affected_wires :
				self.editor.update_connection(*(k + (False,)))

	def move(self, e, start) :
		diffX, diffY = (e.x - start.x), (e.y - start.y)
		self.canvas.move(self.window, diffX, diffY)
		self.model.left, self.model.top, r, b = tuple(self.canvas.bbox(self.window))

	def onMouseUpW(self, e) :
		self.start = None
		for k, v in self.affected_wires :
			self.editor.update_connection(*(k + (True,)))
		self.affected_wires = None
		self.editor.manipulating = None

# ------------------------------------------------------------------------------------------------------------

class BlockEditor(Frame, GraphModelListener) :

	# ----------------------------------------------------------------------------------------------------

	def blckMouseDown(self, sender, e) :
		tw = e.widget.find_overlapping(e.x-1, e.y-1, e.x+1, e.y+1)
		if not tw or not tw[0] in sender.window2term :
			return None
		sender.movingObject = sender.window2term[tw[0]]
		#if not self.model.can_move :
		#	return None
		self.start = e
		xo, yo = tuple(self.canv.coords(sender.window))
		self.offset = (e.x + xo, e.y + yo)
		self.line = self.canv.create_line(0, 0, 0, 0, arrow=LAST, arrowshape=(10,10,5))

	def blckMouseMove(self, sender, e) :
		if self.selection :
			#XXX XXX XXX self.move_selection(sender, e)
			return None
		if not sender.movingObject :
			return None
		xo, yo = tuple(self.canv.coords(sender.window))
		self.canv.coords(self.line, self.offset[0], self.offset[1], e.x+xo, e.y+yo)

	def blckMouseUp(self, sender, e) :
		if not sender.movingObject :
			return None
		self.start = None
		srcterm = sender.movingObject
		sender.movingObject = None
		self.canv.delete(self.line)
		self.line = None
		xo0, yo0, ro0, bo0 = tuple(self.canv.bbox(sender.window))
		dstx = e.x + xo0
		dsty = e.y + yo0
		target = list(dropwhile(lambda trgt: not trgt in self.window_index,
			self.canv.find_overlapping(dstx-1, dsty-1, dstx+1, dsty+1)))
		if not target :
			return None
#		print "target", target
		blck = self.window_index[target[0]]

		if isinstance(blck.model.prototype, JointProto) :
			dstterm = Out("", C, 0) if srcterm.direction == INPUT_TERM else In("", C, 0)
			blck.model.terms.append(dstterm)
			self.canv.tag_raise(blck.window)
		else :
			xo1, yo1, ro1, bo1 = tuple(self.canv.bbox(blck.window))
			tdstx = dstx - xo1
			tdsty = dsty - yo1
			term = blck.find_overlapping(tdstx-1, tdsty-1, tdstx+1, tdsty+1)
			if term and term[0] in blck.window2term :
				dstterm = blck.window2term[term[0]]
			else :
				return None

		if blck == sender and srcterm == dstterm :
			return None
				
		if self.model.can_connect(sender.model, srcterm, blck.model, dstterm) :
			self.model.add_connection(sender.model, srcterm, blck.model, dstterm)

	# ----------------------------------------------------------------------------------------------------

	def block_added(self, model) :
		if isinstance(model.prototype, JointProto) :
			b = Joint(self, model)
		else :
			b = Block(self, model)
		self.block_index[model] = b
		self.window_index[b.window] = b

	def block_removed(self, block) :
		window = self.block_index[block].window
		self.canv.delete(window)
		self.block_index.pop(block)
		self.window_index.pop(window)

	def block_changed(self, block, event=None, reroute=False) :
	
#		return None
		
		#for b in self.block_index.values :
		#	if b.model == block :
		#		b.update()
#		print "block_changed", event
		if self.manipulating == None and block in self.block_index : # and not self.move_indication :
#			traceback.print_stack()
			b = self.block_index[block]
#			print b.__class__
			if event and event["p"] in [ "left", "top", "width", "height", "orientation" ] : # and
				b.reshape()
				for k, v in b.get_wires() : #XXX move to reshape?
					self.update_connection(*(k + (reroute,)))
				if self.selection :
					self.resize_selection()


	def connection_added(self, sb, st, tb, tt, deserializing=False) :
		#TODO i/o arrow dir, make it cleaner
		line = self.canv.create_line(0, 0, 0, 0, arrow=LAST, arrowshape=(10,10,5))
		self.connection2line[(sb, st, tb, tt)] = (line, [])

		if deserializing :
#			print self.model.connections_meta
			conn_meta = self.model.get_connection_meta(sb, st, tb, tt)
#			print "connection_added, deserializing, conn_meta=", conn_meta
			if "path" in conn_meta :
				linecoords = conn_meta["path"]
#				print "connection_added:linecoords", linecoords
				self.connection2line[(sb, st, tb, tt)] = (line, linecoords)
				self.canv.coords(line, *linecoords)
			else :
				self.update_connection(sb, st, tb, tt, True)
		else :
			self.update_connection(sb, st, tb, tt, True)

	def connection_removed(self, sb, st, tb, tt) :
		if isinstance(sb.prototype, JointProto) :
			sb.terms.remove(st)
		if isinstance(tb.prototype, JointProto) :
			tb.terms.remove(tt)
		self.canv.delete(self.connection2line[(sb, st, tb, tt)][0])
		self.connection2line.pop((sb, st, tb, tt))

	# ----------------------------------------------------------------------------------------------------
	
	def update_connection(self, sb, st, tb, tt, fullroute) :
		line, path = self.connection2line[(sb, st, tb, tt)]

		s0 = st.get_location_on_block(sb)
		t0 = tt.get_location_on_block(tb)

		bump = cfg.BLOCK_WIRE_STUB
		bumps = { N: (0, -bump), S: (0, bump), W: (-bump, 0), E: (bump, 0), C: (0, 0) }

		bump0x, bump0y = bumps[st.get_side(sb)]
		s = autoroute.pnt(int(s0[0]+bump0x), int(s0[1]+bump0y))

		bump1x, bump1y = bumps[tt.get_side(tb)]
		t = autoroute.pnt(int(t0[0]+bump1x), int(t0[1]+bump1y))
		
		route = None
		if fullroute :
			r1 = (autoroute.rct(sb.left, sb.top, sb.width, sb.height) if st.get_side(sb) != C
				else autoroute.rct(sb.left, sb.top, 1, 1))
			r2 = (autoroute.rct(tb.left, tb.top, tb.width, tb.height) if tt.get_side(tb) != C
				else autoroute.rct(tb.left, tb.top, 1, 1))
			bbox = autoroute.choose_bbox(r1, r2,
				autoroute.rct(*self.canvas_scrollregion), bump + 1)
			route = autoroute.mtroute_simple(s, t, bbox, r1, r2)
		
		if route :
			linecoords = reduce(lambda w, p: w + [ p[0], p[1] ],
				route, list(s0)) + [ t0[0], t0[1] ]
		else :
			linecoords = [ s0[0], s0[1], s[0], s[1], t[0], t[1], t0[0], t0[1] ]

		self.connection2line[(sb, st, tb, tt)] = (line, linecoords)
		self.canv.coords(line, *linecoords)
		self.model.set_connection_meta(sb, st, tb, tt, { "path" : linecoords })

	# ----------------------------------------------------------------------------------------------------

	#TODO line_edit_data = namedtuple("line_edit_data", ["x"])
	
	def get_nearest(self, x, y, ssz = 4) :
		o = self.canv.find_overlapping(x-ssz, y-ssz, x+ssz, y+ssz)
		return ((o, filter(lambda v: o[0] == v[1][0], self.connection2line.items()))
			if o else (None, None))

	def default_mousedown(self, ee) :
		e = event_t(self.canv.canvasx(ee.x), self.canv.canvasy(ee.y), ee.state)
		
		self.canv.focus_set()
		self.clear_selection()
		if self.manipulating or e.state & BIT_SHIFT:
			return None
		self.move_start = e
		self.manipulating = False
		o, item = self.get_nearest(e.x, e.y)
		if item :
			route = item[0][1][1] # XXX XXX XXX fuckoff!!!
			kneebonus = 4
			indices = xrange(0, len(route)-2, 2)
			dist = chain(
				imap(lambda i: ((i, 2),
					mathutils.pldist(route[i], route[i+1], route[i+2], route[i+3], e.x, e.y)),
						indices),
				imap(lambda i: ((i, 1),
					mathutils.ppdist(route[i], route[i+1], e.x, e.y) - kneebonus),
						indices))

			segment, dist = reduce(lambda a,b: a if a[1] < b[1] else b, dist)
			self.mdata2 = segment

			if e.state & BIT_CONTROL and segment[1] == 2 :

				dist, (knee_x, knee_y) = mathutils.pldistex(
					route[self.mdata2[0]], route[self.mdata2[0]+1],
					route[self.mdata2[0]+2], route[self.mdata2[0]+3],
					e.x, e.y)
				item[0][1][1].insert(self.mdata2[0]+2, knee_y)
				item[0][1][1].insert(self.mdata2[0]+2, knee_x)
				self.mdata2 = (self.mdata2[0]+2, 1)

			self.manipulating = "connection"
			self.mdata = item[0]
		else :
			self.selection_rect = self.create_selection_rect(e.x, e.y, e.x, e.y)
#			self.create_selection([])

	def default_mousemove(self, ee) :
		e = event_t(self.canv.canvasx(ee.x), self.canv.canvasy(ee.y), ee.state)

		if self.manipulating == "connection" :
			diffX, diffY = (e.x - self.move_start.x), (e.y - self.move_start.y)
			self.move_start = e
			indices = xrange(self.mdata2[0], self.mdata2[0]+(self.mdata2[1]*2), 2)
			for i in indices :
				if i > 0 and (i+2)<len(self.mdata[1][1]) :
					self.mdata[1][1][i] += diffX
					self.mdata[1][1][i+1] += diffY

			#self.connection2line[(sb, st, tb, tt)] = (line, linecoords)
			self.canv.coords(self.mdata[1][0], *self.mdata[1][1])
		elif self.selection_rect != None :
			self.canv.coords(self.selection_rect, self.move_start.x, self.move_start.y, e.x, e.y)

	def default_mouseup(self, ee) :
		e = event_t(self.canv.canvasx(ee.x), self.canv.canvasy(ee.y), ee.state)

#		add_to_selection = None
#		if self.manipulating == None and e.state & BIT_SHIFT :
#			add_to_selection, itm = self.get_nearest(e.x, e.y)
#			if not self.selection_rect :
#				self.move_start = e
#				self.selection_rect = self.create_selection_rect(e.x, e.y, e.x, e.y)

		self.manipulating = None
		self.mdata = None
		self.mdata2 = None

		if self.move_start :
			self.create_selection_from_area(self.move_start.x, self.move_start.y, e.x, e.y)

	# ----------------------------------------------------------------------------------------------------

	def add_to_selection(self, blocks) :
		pass # TODO

	def create_selection_from_list(self, blocks, lines) :
		self.clear_selection()
#		print blocks, "\n\n", lines
		if blocks or lines :
			x, y, r, b, = self.measure_objects(blocks, lines)
			self.selection_rect = self.create_selection_rect(x, y, r, b)
			self.selection = selection_t(blocks, lines)
			self.resize_selection()

	def create_selection_from_area(self, x, y, r, b) :
		self.clear_selection()
		selected = self.canv.find_enclosed(x, y, r, b)
		if selected :
			blcks = filter(None, imap(
				lambda w: self.window_index[w] if w in self.window_index else None,
					selected)) # blocks and joints
			lns = filter(lambda v: v[1][0] in selected, self.connection2line.items())
			self.create_selection_from_list(blcks, lns)

	def select_all(self) :
		self.create_selection_from_list(self.window_index.values(), self.connection2line.items())

	def measure_selection(self) :
		if self.selection :
			return self.measure_objects(self.selection.blocks, self.selection.lines)
		return None

	def measure_objects(self, selected_blocks, selected_lines) :
		blocks, lines = None, None
		if selected_lines :
			lines = reduce(mathutils.max_rect,
				imap(lambda l: self.canv.bbox(l[1][0]), selected_lines))
		if selected_blocks :
			blocks = reduce(mathutils.max_rect,
				imap(lambda b: self.canv.bbox(b.window), selected_blocks))
		if blocks and lines :
			return mathutils.max_rect(blocks, lines) 
		else :
			return blocks if blocks else lines

	def resize_selection(self) :
		b = self.measure_selection()
		m = cfg.SELECTION_RECT_SIZE
		self.canv.coords(self.selection_rect, b[0]-m, b[1]-m, b[2]+m, b[3]+m)

	def create_selection_rect(self, x0, y0, x1, y1) :
		return self.canv.create_rectangle(x0, y0, x1, y1, dash=(2,2), fill=None)

	def clear_selection(self) :
		if self.selection_rect :
			self.canv.delete(self.selection_rect)
			self.selection_rect = None
			self.selection = None

	def delete_selection(self) :
		if self.selection :
			for connection, data in self.selection.lines :
				self.model.remove_connection(*connection)
			for block in self.selection.blocks :
				self.model.remove_block(block.model)
			self.clear_selection()

	#TODO optimize (blockmodel.geo = (pos, size, angles) ...)
	#XXX blockmodel.transform?
	#XXX create editor model/move to dfs?
	def rotate_selection(self, x, y, z) :
		# assuming rotation around only one axis at a time
		if self.selection :
			sx, sy, sw, sh = self.measure_selection()
#			orgx, orgy = sx+((sw-sx)*0.5), sy+((sh-sy)*0.5)
			orgx, orgy = sx+((sw-sx)/2), sy+((sh-sy)/2)
			for b in self.selection.blocks :
				#XXX BlockModel.rotate(self, angles, origin) ?
				m = b.model
				x0, y0, z0 = m.orientation
				l, t = ll, tt = m.center
				if z :
					l, t = mathutils.rotate4(orgx, orgy, ll, tt, (z+360)%360)
				elif x :
					t = (2 * (orgy - tt)) + tt
				elif y:
					l = (2 * (orgx - ll)) + ll
				m.orientation = (x0+x+360)%360, (y0+y+360)%360, (z0+z+360)%360
#				print "m.orientation", m.orientation
				m.center = l, t

	#XXX editor model?
	def move_selection(self, x, y) :
		if self.selection :
			for b in self.selection.blocks :
				if x :
					b.model.left += x
				if y :
					b.model.top += y
			self.resize_selection()

	def select_next(self) :
		if self.selection :
			print "TODO select_next"

	# ----------------------------------------------------------------------------------------------------

	def serialize_selection(self) :
		if self.selection :
#			print "TODO get_serialized_selection"
#		blocks, connections, connections_meta, model_meta
#			print self.selection.lines

			conns = [ ((b0, t0), [(b1, t1)]) for ((b0, t0, b1, t1), _) in self.selection.lines ]
#			conns = [ ldata[0] for ldata, _ in self.selection.lines ]			

#			print conns
			data = get_dfs_model_data2(
				[ b.model for b in self.selection.blocks ],
				dict(conns),
				dict([ (k, self.model.connections_meta[k]) for k, _ in self.selection.lines ]),
#				[ self.model.connections_meta[k+v] for k, v in conns ],
				{} )
			return pickle.dumps(data)

#	def paste_enum()

	def paste(self, serialized) :
		if self.selection :
			self.clear_selection()
		try :
			types, struct, meta = pickle.loads(serialized)
		except :
			return None
		
		load_to_dfs_model(self.model, types, struct, meta)
		return None

		m = restore_dfs_model(types, struct, meta)
		m.add_listener(self)
		m.enum(deserializing=True)
#		self.model.merge(m)
		blocks, lines = [ self.block_index[b] for b in m.blocks ], []
#		print self.window_index

		self.create_selection_from_list(blocks, lines)
		

	# ----------------------------------------------------------------------------------------------------

	def paste_block_on_mouse_down(self, prototype, e) :
		b = BlockModel(prototype, self.model, left=e.x, top=e.y)
		self.model.add_block(b)
		if not bool(e.state & BIT_SHIFT) : #XXX
			self.canv.bind("<ButtonPress-1>", self.default_mousedown)

	# ----------------------------------------------------------------------------------------------------

#	def get_serialized_selection(self) :
#		if self.selection :
#			print "TODO get_serialized_selection"
##		blocks, connections, connections_meta, model_meta
##			self.selection.blocks, self.selection.lines

	def get_model(self) :
		return self.model

	def set_model(self, model, deserializing=False) :
		self.reset_state()
		if model :
			self.set_model(None)
			self.model = model
			self.model.add_listener(self)
			self.undo = undo.UndoListener(self.model, None, None)
			self.model.add_listener(self.undo)
			self.model.enum(deserializing=deserializing)
		else :
			if self.model :
				self.model.remove_listener(self)
				self.model.remove_listener(self.undo)
				self.undo = None
			self.model = None
			self.canv.delete(ALL)

	def set_changed(self, v) :
		self.undo.set_changed(False)

	changed = property(lambda self: self.undo.changed if self.model else False, set_changed)

	def reset_state(self) :
		self.manipulating = None
		self.move_start = None
		self.selection_rect = None
		self.selection = None
		self.model = None
		self.block_index = {}
		self.window_index = {}
		self.connection2line = {}
		self.joints_index = {}
#		self.move_indication = False

	def __init__(self, parent) :

		self.__changed = False

		Frame.__init__(self, parent)

		self.grid(column=0, row=0, sticky=(N, W, E, S))

		self.canvas_scrollregion = (0, 0, cfg.CANVAS_WIDTH, cfg.CANVAS_HEIGHT)
		self.canv = Canvas(self, scrollregion=self.canvas_scrollregion, bg="white")
		self.canv.grid(column=0, row=0, sticky=(W, E, N, S))
		self.canv.columnconfigure(0, weight=1)
		self.canv.rowconfigure(0, weight=1)

		yscroll = Scrollbar(self, orient=VERTICAL, command=self.canv.yview)
		yscroll.grid(column=1, row=0, sticky=(N,S))
		self.canv.configure(yscrollcommand=yscroll.set)

		xscroll = Scrollbar(self, orient=HORIZONTAL, command=self.canv.xview)
		xscroll.grid(column=0, row=1, sticky=(W,E))
		self.canv.configure(xscrollcommand=xscroll.set)

		self.reset_state()

		#TODO actions, look at gtk
		self.canv.bind("<ButtonPress-1>", self.default_mousedown)
		self.canv.bind("<B1-Motion>", self.default_mousemove)
		self.canv.bind("<ButtonRelease-1>", self.default_mouseup)
		self.canv.bind("<Delete>", lambda a: self.delete_selection())
		self.canv.bind("<Escape>", lambda a: self.clear_selection())
		self.canv.bind("<l>", lambda a: self.rotate_selection(0, 0, -90))
		self.canv.bind("<r>", lambda a: self.rotate_selection(0, 0, 90))
		self.canv.bind("<h>", lambda a: self.rotate_selection(0, 180, 0))
		self.canv.bind("<v>", lambda a: self.rotate_selection(180, 0, 0))
		self.canv.bind("<Left>", lambda a: self.move_selection(-cfg.GRID_SIZE, 0))
		self.canv.bind("<Right>", lambda a: self.move_selection(cfg.GRID_SIZE, 0))
		self.canv.bind("<Up>", lambda a: self.move_selection(0, -cfg.GRID_SIZE))
		self.canv.bind("<Down>", lambda a: self.move_selection(0, cfg.GRID_SIZE))
		self.canv.bind("<Tab>", lambda a: self.select_next())
		
		#XXX cursor: select, shift+cursor: move ?
		
		#self.canv.bind("<Motion>", lambda e: pprint((e.x, e.y)))

# ------------------------------------------------------------------------------------------------------------

class BlockEditorWindow :

	def new_file(self, a=None) :
		self.bloced.set_model(None)
		model = GraphModel()
		self.bloced.set_model(model)
		self.__set_current_file_name(None)

	def open_file(self, a=None) :
		fname = askopenfilename()
		if fname :
			self.open_this_file_new(fname)

	def open_this_file_new(self, fname) :
		try :
			f = open(fname, "rb")
			mdl = unpickle_dfs_model(f)
			f.close()
			self.bloced.set_model(mdl, deserializing=True)
			self.__set_current_file_name(fname)
			self.bloced.changed = False
		except IOError :
			print("IOError")

	def save_file(self, fname) :
		if fname :
			try :
				f = open(fname, "wb")
				pickle_dfs_model(self.bloced.get_model(), f)
				f.close()
				self.__set_current_file_name(fname)
				self.bloced.changed = False
				return True
			except IOError :
				print("IOError")
		return False

	def save_file_as(self) :
		return self.save_file(asksaveasfilename())

	def save_current_file(self, a=None) :
		return self.save_file(self.current_filename if self.have_file else asksaveasfilename())

	def mnu_edit_cut(self, a=None) :
		if self.bloced.selection :
			pyperclip.setcb(self.bloced.serialize_selection())
			self.bloced.delete_selection()

	def mnu_edit_copy(self, a=None) :
		if self.bloced.selection :
			pyperclip.setcb(self.bloced.serialize_selection())

	def mnu_edit_paste(self, a=None) :
		self.bloced.paste(pyperclip.getcb())

	def mnu_edit_delete(self, a=None) :
		self.bloced.delete_selection()

	def mnu_edit_undo(self, a=None) :
		if self.bloced.undo :
			self.bloced.undo.undo()

	def mnu_edit_redo(self, a=None) :
		if self.bloced.undo :
			self.bloced.undo.redo()

	def mnu_edit_preferences(self, a=None) :
		pass

	def mnu_edit_select_all(self, a=None) :
		self.bloced.select_all()

	def mnu_edit_comment(self, a=None) :
		pass

	def mnu_edit_uncomment(self, a=None) :
		pass

	def begin_paste_block(self, prototype) : # TODO weird, make it not weird
		self.bloced.canv.bind("<ButtonPress-1>",
			partial(self.bloced.paste_block_on_mouse_down, prototype))

	def mnu_blocks_insert_last(self) :
		print "TODO mnu_blocks_insert_last"

	def implement(self) :
		out = implement_dfs(self.bloced.get_model(), None)
		print "out:", out

	def close_window(self, a=None) :
		if self.file_changed :
			ans = tkMessageBox.askquestion(type=tkMessageBox.YESNOCANCEL, title=cfg.APP_NAME,
				message=cfg.SAVE_BEFORE_CLOSE, default=tkMessageBox.YES)
			if ans == tkMessageBox.CANCEL:
				return None
			elif ans == tkMessageBox.YES :
				if not self.save_current_file() :
					return None
		self.root.destroy()

	def __on_closing(self) :
		self.close_window()

	def __convert_mnu_text(self, text) :
		under = text.find("&")
		return ( text[0:under]+text[under+1:] if under != -1 else text,
			 under if under != -1 else None )

	def __convert_accel(self, accel) :
		parts = accel.replace("Ctrl", "Control").split("+")
		parts[-1] = parts[-1].lower() if len(parts[-1]) == 1 else parts[-1]
		return "<" + string.join(parts, "-") + ">"
		
	def __add_submenu_item(self, parent, text, accel, handler, items=[]) :
		txt, under = self.__convert_mnu_text(text)
		if accel :
			self.root.bind(self.__convert_accel(accel), handler)
		return parent.add_command(label=txt, underline=under,
			command=handler, accelerator=accel)

	def __add_top_menu(self, text, items=[]) :
		mnu = Menu(self.__menubar)
		txt, under = self.__convert_mnu_text(text)
		self.__menubar.add_cascade(menu=mnu, label=txt, underline=under)
		for item in items :
			if item == "-" :
				mnu.add_separator()
			else :
				self.__add_submenu_item(*((mnu, )+item))
		return mnu

	def __set_current_file_name(self, fname) :
		self.__fname = fname
		if fname :
			self.root.title("%s (%s) - %s" % (os.path.basename(fname),
				os.path.dirname(fname), cfg.APP_NAME))
		else :
			self.root.title(cfg.NONE_FILE + " - " + cfg.APP_NAME)

	file_changed = property(lambda self: self.bloced.changed, lambda self, v: self.bloced.set_changed(v))
	have_file = property(lambda self: self.__fname != None)
	current_filename = property(lambda self: self.__fname)

	def __init__(self) :

		self.__fname = None

		self.root = Tk()
		self.root.protocol("WM_DELETE_WINDOW", self.__on_closing)
#		print (tkFont.Font().actual())
#		print tkFont.families()

		self.root.title(cfg.APP_NAME)
		self.root.option_add("*tearOff", FALSE)
		self.root.geometry("800x600")
		self.root.columnconfigure(0, weight=1)
		self.root.rowconfigure(0, weight=1)

		mainframe = Frame(self.root)
		mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
		mainframe.columnconfigure(0, weight=1)
		mainframe.rowconfigure(0, weight=0)
		mainframe.rowconfigure(1, weight=1)

		self.bloced = BlockEditor(mainframe)
		self.bloced.grid(column=0, row=1, sticky=(W, E, N, S))
		self.bloced.columnconfigure(0, weight=1)
		self.bloced.rowconfigure(0, weight=1)

		self.blockfactory = create_block_factory()

		self.__menubar = Menu(self.root)
		self.root["menu"] = self.__menubar

		self.__add_top_menu("&File", [
			("&New", "Ctrl+N", self.new_file),
			("&Open...", "Ctrl+O", self.open_file),
			("&Save", "Ctrl+S", self.save_current_file),
			("S&ave As...", "Shift+Ctrl+S", self.save_file_as),
#			"-",
#			("Export...", "Ctrl+E", self.__mnu_file_export),
			"-",
			("&Quit", "Alt+F4", self.close_window) ])

		self.__add_top_menu("&Edit", [
			("&Undo", "Ctrl+Z", self.mnu_edit_undo),
			("&Redo", "Shift+Ctrl+Z", self.mnu_edit_redo),
			"-",
			("Cu&t", "Ctrl+X", self.mnu_edit_cut),
			("&Copy", "Ctrl+C", self.mnu_edit_copy),
			("&Paste", "Ctrl+V", self.mnu_edit_paste),
			("&Delete", "Delete", self.mnu_edit_delete),
			"-",
			("Select &All", "Ctrl+A", self.mnu_edit_select_all),
			"-",
			("Co&mment Selection", "Ctrl+M", self.mnu_edit_comment),
			("U&ncomment Selection", "Shift+Ctrl+M", self.mnu_edit_uncomment),
			"-",
			("Pr&eferences", None, self.mnu_edit_preferences) ])

		menu_blocks = self.__add_top_menu("&Insert", [
			("&Insert last", "Ctrl+I", self.mnu_blocks_insert_last),
			"-" ])
		for cat, b_iter in groupby(self.blockfactory.block_list, lambda b: b.category) :
			submenu = Menu(menu_blocks)
			menu_blocks.add_cascade(label=cat, menu=submenu)
			for proto in b_iter :
				submenu.add_command(label=proto.type_name,
				command=partial(self.begin_paste_block, proto))

		self.__add_top_menu("&Model", [
			("&Verify", "F6", None),
			("&Run", "F5", None),
			("&Stop", "Ctrl+F5", None)])

		self.__add_top_menu("&Help", [
			("&Content...", "F1", None),
			"-",
			("&About...", None, None) ])

		self.__add_top_menu("_Debu&g", [
			("Implement", None, self.implement),
			("connections", None, lambda: pprint(self.bloced.get_model().get_connections())) ])
#		menu_debug.add_command(label="zoom",
#			command=lambda: self.bloced.canv.scale(ALL, 0, 0, 2, 2))

		self.new_file()

# ------------------------------------------------------------------------------------------------------------

if __name__ == "__main__" :
	be = BlockEditorWindow()
	if len(sys.argv) == 2 :
		be.open_this_file_new(os.path.abspath(os.path.join(os.path.curdir, sys.argv[1])))
	be.root.mainloop()

# ------------------------------------------------------------------------------------------------------------

