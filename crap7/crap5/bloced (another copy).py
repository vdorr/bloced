
from Tkinter import * 
from pprint import pprint
from collections import namedtuple
import autoroute
from tkFileDialog import askopenfilename, asksaveasfilename
from sys import exit
from dfs import *
from functools import partial
from math import sqrt
from itertools import ifilter, imap, chain, dropwhile
from serializer import pack_dfs_model, unpack_dfs_model, pack_dfs_model_new, unpack_dfs_model_new
from implementer import implement_dfs
import argparse

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

	def onDblClick(self, e) :
		#if isinstance(self.model.prototype, ConstProto) :
		if type(self.model.prototype) in (ConstProto, DelayProto) :
			entry = Entry(self)
			entry.insert(0, str(self.model.get_value()))
			w = self.create_window(0, 0, window=entry, anchor=NW)
			entry.bind("<Return>", lambda e: self.close_editor(True, w, entry))
			entry.bind("<Escape>", lambda e: self.close_editor(False, w, entry))
			entry.pack(side=LEFT, fill=X)
			entry.focus()

	def close_editor(self, accept, w, entry) :
		if accept :
			self.model.set_value(str(entry.get()))
			self.update_text()
		self.delete(w)
		entry.destroy()
		self.config(width=self.model.width, height=self.model.height, bg="white",
			borderwidth=0, highlightthickness=0)

	def update_text(self) :
		if type(self.model.prototype) == ConstProto :
			newtxt = self.model.get_value()
		elif type(self.model.prototype) == DelayProto :
			newtxt = "Delay (" + self.model.get_value() + ")"
		else :
			newtxt=self.model.caption
		self.itemconfigure(self.caption_txt, text=newtxt)

	def __init__(self, editor, model) :
		self.editor = editor
		self.canvas = editor.canv
		self.model = model
		
		Canvas.__init__(self, self.editor.canv, width=self.model.width,
			height=self.model.height, bg="white",
			borderwidth=0, highlightthickness=0)

		self.window = self.canvas.create_window(self.model.left, self.model.top,
			window=self, anchor=NW)

		self.caption_txt = self.create_text(0, 0, anchor=NW)
		self.update_text()

		self.create_rectangle(0, 0, self.model.width - 1, self.model.height - 1)
		
		self.movingObject = None
		self.bind("<B1-Motion>", self.onMouseMoveW)
		self.bind("<ButtonPress-1>", self.onMouseDownW)
		self.bind("<ButtonRelease-1>", self.onMouseUpW)
		self.bind("<Configure>", self.onConfigure)
		self.bind("<Double-Button-1>", self.onDblClick)

		tsz = 12
		sides = {
			N : lambda p: (self.model.width*p-tsz/2, 0),
			S : lambda p: (self.model.width*p-tsz/2, self.model.height-tsz),
			W : lambda p: (0, self.model.height*p-tsz/2),
			E : lambda p: (self.model.width-tsz-1, self.model.height*p-tsz/2),
			C : lambda p: (0.5*self.model.width, 0.5*self.model.height),
		}
		self.window2term = {}
		for t in self.model.terms :
			x, y = sides[t.side](t.pos)
			
			o = self.create_rectangle(x, y, x + tsz, y + tsz, fill="black", tags=t.name)
			self.bind_as_term(o)
			
			txt = self.create_text(x, y, text=t.name, anchor=NW, fill="white")
			self.bind_as_term(txt)
			
			self.window2term[o] = t

		self.affected_wires = None

	def bind_as_term(self, o) :
		self.tag_bind(o, "<B1-Motion>", self.onMouseMove)#TODO use partial(
		self.tag_bind(o, "<ButtonPress-1>", self.onMouseDown)
		self.tag_bind(o, "<ButtonRelease-1>", self.onMouseUp)

	def onMouseDownW(self, e) :
		self.start = e
		self.affected_wires = filter(lambda c: self.model in (c[0][0], c[0][2]), #sb, st, tb, tt
			self.editor.connection2line.items())
		for k, v in self.affected_wires :
			self.editor.update_connection(*(k + (False,)))

	def onMouseMoveW(self, e) :
		if not self.movingObject and self.start :
			self.canvas.move(self.window, e.x - self.start.x, e.y - self.start.y)
			for k, v in self.affected_wires :
				self.editor.update_connection(*(k + (False,)))

	def onMouseUpW(self, e) :
		self.start = None
		if not self.affected_wires :
			return None
		for k, v in self.affected_wires :
			self.editor.update_connection(*(k + (True,)))
		self.affected_wires = None

	def onConfigure(self, e) :
		self.model.left, self.model.top, r, b = tuple(self.canvas.bbox(self.window))

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

	def onMouseDownW(self, e) :
		if self.editor.manipulating :
			return None
		self.editor.manipulating = "joint"
		self.start = e
		self.affected_wires = filter(lambda c: self.model in (c[0][0], c[0][2]), #sb, st, tb, tt
			self.editor.connection2line.items())
		for k, v in self.affected_wires :
			self.editor.update_connection(*(k + (False,)))

	def onMouseMoveW(self, e) :
		if not self.movingObject and self.editor.manipulating == "joint" :
			diffX, diffY = (e.x - self.start.x), (e.y - self.start.y)
			self.canvas.move(self.window, diffX, diffY)
			self.start = e
			self.model.left, self.model.top, r, b = tuple(self.canvas.bbox(self.window))
			for k, v in self.affected_wires :
				self.editor.update_connection(*(k + (False,)))

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

	def move_selection(self, sender, e) :
		#xo, yo = tuple(self.canv.coords(sender.window))
		#self.canv.coords(self.line, self.offset[0], self.offset[1], e.x+xo, e.y+yo)
		pass

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
		print "target", target
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

	def block_changed(self, block) :
		#for b in self.block_index.values :
		#	if b.model == block :
		#		b.update()
		pass

	def connection_added(self, sb, st, tb, tt) :
		line = self.canv.create_line(0, 0, 0, 0, arrow=LAST, arrowshape=(10,10,5))#TODO i/o arrow dir
		self.connection2line[(sb, st, tb, tt)] = (line, [])
		self.update_connection(sb, st, tb, tt, True)

	def connection_removed(self, sb, st, tb, tt) :
		if isinstance(sb.prototype, JointProto) :
			sb.terms.remove(st)
		if isinstance(tb.prototype, JointProto) :
			tb.terms.remove(tt)
		self.canv.delete(self.connection2line[(sb, st, tb, tt)][0])

	# ----------------------------------------------------------------------------------------------------
	
	def update_connection(self, sb, st, tb, tt, fullroute) :
		line, path = self.connection2line[(sb, st, tb, tt)]

		s0 = self.get_term_outside_location(sb.left, sb.top, st, sb)
		t0 = self.get_term_outside_location(tb.left, tb.top, tt, tb)

		bump = 16
		bumps = { N: (0, -bump), S: (0, bump), W: (-bump, 0), E: (bump, 0), C: (0, 0) }

		bump0x, bump0y = bumps[st.side]
		s = autoroute.pnt(s0[0] + bump0x, s0[1] + bump0y)

		bump1x, bump1y = bumps[tt.side]
		t = autoroute.pnt(t0[0] + bump1x, t0[1] + bump1y)

		route = None
		if fullroute :
			r1 = (autoroute.rct(sb.left, sb.top, sb.width, sb.height) if st.side != C
				else autoroute.rct(sb.left, sb.top, 1, 1))
			r2 = (autoroute.rct(tb.left, tb.top, tb.width, tb.height) if tt.side != C
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

	#TODO move to TermModel
	def get_term_outside_location(self, xo, yo, t, bm) :
		sides = {
			N : lambda: (int(xo + t.pos * bm.width), yo),
			S : lambda: (int(xo + t.pos * bm.width), yo + bm.height),
			W : lambda: (xo, int(yo + t.pos * bm.height)),
			E : lambda: (xo + bm.width, int(yo + t.pos * bm.height)),
			C : lambda: (xo + 0.5 * bm.width, int(yo + 0.5 * bm.height)),
		}
		return sides[t.side]()

	def get_model(self) :
		return self.model

	def set_model(self, model) :
		if model :
			self.set_model(None)
			self.model = model
			self.model.add_listener(self)
			self.model.enum()
		else :
			if self.model :
				self.model.remove_listener(self)
			self.model = None
			self.canv.delete(ALL)

	# ----------------------------------------------------------------------------------------------------

	#TODO line_edit_data = namedtuple("line_edit_data", ["x"])
	
	def pldist(self, x1, y1, x2, y2, x, y) :
		#print "x1, y1, x2, y2, x, y", x1, y1, x2, y2, x, y #XXX
		n0, n1 = -y2+y1, x2-x1
		den = sqrt((n0**2)+(n1**2))
		return abs((x*n0)+(y*n1)+-(x1*n0)-(y1*n1))/den if den else self.ppdist(x1, y1, x, y)

	def pldistex(self, x1, y1, x2, y2, x, y) :
		#print "x1, y1, x2, y2, x, y", x1, y1, x2, y2, x, y #XXX
		n0, n1 = -y2+y1, x2-x1
		den = sqrt((n0**2)+(n1**2))
#		print "xxx:", (x*n0) / den, (y*n1) / den, (x1*n0) / den, (y1*n1) / den
		dist =  ((x*n0)+(y*n1)+-(x1*n0)-(y1*n1))/den if den else self.ppdist(x1, y1, x, y)
		#print x-((dist*n0)/den), y-((dist*n1)/den)
		return namedtuple("pldist", ["dist", "intsc"])(
			abs(dist), (x-((dist*n0)/den), y-((dist*n1)/den)))

	def ppdist(self, x1, y1, x2, y2) :
		return sqrt((x1-x2)**2+(y1-y2)**2)
	
	def insert_point_to_route(self, route, i, x, y) :
		return route[:i*2] + [x, y] + route[i*2:]

	def default_mousedown(self, e) :
		self.canv.focus_set()
		self.clear_selection()
		if self.manipulating :
			return None
		#print e.state #TODO
		self.move_start = e
		self.manipulating = False
		ssz = 4
		o = self.canv.find_overlapping(e.x-ssz, e.y-ssz, e.x+ssz, e.y+ssz)
		if not o :
			self.selection_rect = self.canv.create_rectangle(e.x, e.y, e.x, e.y,
				dash=(2,2), fill=None)
			return None
		item = filter(lambda v: o[0] == v[1][0], self.connection2line.items())
		if item :

			route = item[0][1][1]#XXX XXX XXX fuckoff!!!
			
			kneebonus = 4
			indices = xrange(0, len(route)-2, 2)
			print "indices", list(indices)

			dist = chain(
				imap(lambda i: (
					(i, 2),
					self.pldist(route[i], route[i+1], route[i+2], route[i+3], e.x, e.y)),
						indices),
				imap(lambda i: (
					(i, 1),
					self.ppdist(route[i], route[i+1], e.x, e.y) - kneebonus),
						indices))
					
					
#			dist = list(dist)
#			print dist
			segment, dist = reduce(lambda a,b: a if a[1] < b[1] else b, dist)
			self.mdata2 = segment

			if e.state & BIT_CONTROL and segment[1] == 2 :

				dist, (knee_x, knee_y) = self.pldistex(
					route[self.mdata2[0]], route[self.mdata2[0]+1],
					route[self.mdata2[0]+2], route[self.mdata2[0]+3],
					e.x, e.y)

				print "knee_x, knee_y", knee_x, knee_y
				#TODO add point and set self.mdata2 to its index
				#item[0][1][1] = self.insert_point_to_route(route, self.mdata2[0], knee_x, knee_y)
				
				print item[0][1][1]
				print self.mdata2[0]
				
				item[0][1][1].insert(self.mdata2[0]+2, knee_y)
				item[0][1][1].insert(self.mdata2[0]+2, knee_x)
				self.mdata2 = (self.mdata2[0]+2, 1)

			self.manipulating = "connection"
			self.mdata = item[0]


			print "self.mdata2", self.mdata2, "e.state", hex(e.state)

	def default_mousemove(self, e) :
		if self.manipulating == "connection" :
			diffX, diffY = (e.x - self.move_start.x), (e.y - self.move_start.y)
			self.move_start = e

			indices = xrange(self.mdata2[0], self.mdata2[0]+(self.mdata2[1]*2), 2)
			
#			print "move/indices", list(indices)
			
			for i in indices :
				if i > 0 and (i+2)<len(self.mdata[1][1]) :
					self.mdata[1][1][i] += diffX
					self.mdata[1][1][i+1] += diffY

			#self.connection2line[(sb, st, tb, tt)] = (line, linecoords)
			self.canv.coords(self.mdata[1][0], *self.mdata[1][1])
		elif self.selection_rect != None :
			self.canv.coords(self.selection_rect,
				self.move_start.x, self.move_start.y, e.x, e.y)

	def default_mouseup(self, e) :
		self.manipulating = None
		self.mdata = None
		self.mdata2 = None
		if self.selection_rect != None :
			#XXX self.selection_rect = None
			selected = self.canv.find_enclosed(
				self.move_start.x, self.move_start.y, e.x, e.y)
			if selected :
				b = reduce(lambda a,b: (
					b[0] if b[0] < a[0] else a[0],
					b[1] if b[1] < a[1] else a[1],
					b[2] if b[2] > a[2] else a[2],
					b[3] if b[3] > a[3] else a[3]),
						map(lambda o: self.canv.bbox(o), selected))
				m = 4
				self.canv.coords(self.selection_rect, b[0]-m, b[1]-m, b[2]+m, b[3]+m)
				
				snt = namedtuple("snt", [ "blocks", "lines", "joints"]);
				blcks = filter(None, imap(
					lambda w: self.window_index[w] if w in self.window_index else None,
						selected)) # blocks and joints
				lns = filter(lambda v: v[1][0] in selected, self.connection2line.items())
				self.selection = snt(blcks, lns, None)

			else :
				self.canv.delete(self.selection_rect)

	# ----------------------------------------------------------------------------------------------------

	def clear_selection(self) :
		if self.selection :
			self.canv.delete(self.selection_rect)
			self.selection_rect = None
			self.selection = None

	def move_selection(self, e) :
		if self.selection :
			pass

	def delete_selection(self) :
		if self.selection :
			for connection, data in self.selection.lines :
				self.model.remove_connection(*connection)
				#print l, ll
			for block in self.selection.blocks :
				self.model.remove_block(block.model)
			self.clear_selection()

	# ----------------------------------------------------------------------------------------------------

	def paste_block_on_mouse_down(self, prototype, e) :
		#b = BlockModel(prototype.get_type_name(), e.x, e.y,
		#	prototype.default_size[0], prototype.default_size[1],
		#	prototype.get_terms())
		b = BlockModel(prototype, left=e.x, top=e.y)
		self.model.add_block(b)
		if not bool(e.state & BIT_SHIFT) : #XXX
			self.canv.bind("<ButtonPress-1>", self.default_mousedown)

	# ----------------------------------------------------------------------------------------------------

	def key_escape(self, e) :
		if self.selection :
			self.clear_selection()

	def key_delete(self, e) :
		if self.selection :
			self.delete_selection()

	def __init__(self, parent) :

		Frame.__init__(self, parent)

		self.grid(column=0, row=0, sticky=(N, W, E, S))

		self.canvas_scrollregion = (0, 0, 2048, 2048)
		self.canv = Canvas(self, scrollregion=self.canvas_scrollregion, bg="white")
		self.canv.grid(column=0, row=0, sticky=(W, E, N, S))
		self.canv.columnconfigure(0, weight=1)
		self.canv.rowconfigure(0, weight=1)
		#self.canv.bind("<Motion>", lambda e: pprint((e.x, e.y)))

		yscroll = Scrollbar(self, orient=VERTICAL, command=self.canv.yview)
		yscroll.grid(column=1, row=0, sticky=(N,S))
		self.canv.configure(yscrollcommand=yscroll.set)

		xscroll = Scrollbar(self, orient=HORIZONTAL, command=self.canv.xview)
		xscroll.grid(column=0, row=1, sticky=(W,E))
		self.canv.configure(xscrollcommand=xscroll.set)

		self.canv.bind("<ButtonPress-1>", self.default_mousedown)
		self.canv.bind("<B1-Motion>", self.default_mousemove)
		self.canv.bind("<ButtonRelease-1>", self.default_mouseup)
		self.canv.bind("<Delete>", self.key_delete)
		self.canv.bind("<Escape>", self.key_escape)

		self.manipulating = None
		self.move_start = None
		self.selection_rect = None
		self.selection = None

		self.model = None

		self.block_index = {}
		self.window_index = {}
		self.connection2line = {}
		self.joints_index = {}

# ------------------------------------------------------------------------------------------------------------

class BlockEditorWindow :

	def new_file(self) :
		self.bloced.set_model(None)
		model = GraphModel()
		self.bloced.set_model(model)

	def save_file(self) :
		fname = asksaveasfilename()
		if fname :
			try :
				f = open(fname, "wb")
				mdl = self.bloced.get_model()
				self.bloced.set_model(None)
				pack_dfs_model_new(mdl, f)
				self.bloced.set_model(mdl)
				f.close()
			except IOError :
				print("IOError")

	def open_file_new(self) :
		fname = askopenfilename()
		if fname :
			self.open_this_file_new(fname)

	def open_this_file_new(self, fname) :
		try :
			f = open(fname, "rb")
			mdl = unpack_dfs_model_new(f)
			f.close()
			self.bloced.set_model(mdl)
		except IOError :
			print("IOError")

	def open_file(self) :
		fname = askopenfilename()
		if fname :
			self.open_this_file(fname)

	def open_this_file(self, fname) :
		try :
			f = open(fname, "rb")
			mdl = unpack_dfs_model(f)
			f.close()
			self.bloced.set_model(mdl)
		except IOError :
			print("IOError")
	
	def begin_paste_block(self, prototype) : # TODO weird, make it not weird
		self.bloced.canv.bind("<ButtonPress-1>",
			partial(self.bloced.paste_block_on_mouse_down, prototype))

	def implement(self) :
		out = implement_dfs(self.bloced.get_model(), None)
		print "out:", out

	def __init__(self) :
	
		self.root = Tk()

		self.root.title("bloced")
		self.root.option_add("*tearOff", FALSE)
		self.root.geometry("640x480")
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

		menubar = Menu(self.root)
		self.root["menu"] = menubar
		menu_file = Menu(menubar)
		menubar.add_cascade(menu=menu_file, label="File")
		menu_file.add_command(label="New", command=self.new_file)
		menu_file.add_command(label="Open...", command=self.open_file)
		menu_file.add_command(label="Open new Format...", command=self.open_file_new)
		menu_file.add_command(label="Save As...", command=self.save_file)
		menu_file.add_separator()
		menu_file.add_command(label="Export...", command=None)
		menu_file.add_separator()
		menu_file.add_command(label="Quit", command=self.root.destroy)

		menu_debug = Menu(menubar)
		menubar.add_cascade(menu=menu_debug, label="Debug")
		menu_debug.add_command(label="Implement",
			command=self.implement)
		menu_debug.add_command(label="connections",
			command=lambda: pprint(self.bloced.get_model().get_connections()))
#		menu_debug.add_command(label="zoom",
#			command=lambda: self.bloced.canv.scale(ALL, 0, 0, 2, 2))

		self.blockfactory = create_block_factory()

		menu_blocks = Menu(menubar)
		menubar.add_cascade(menu=menu_blocks, label="Blocks")
		for bp in self.blockfactory.get_block_list() :
			menu_blocks.add_command(label =  bp.get_type_name(),
				command = partial(self.begin_paste_block, bp))

		self.new_file()

# ------------------------------------------------------------------------------------------------------------

#pldist_t = namedtuple("pldist", ["dist", "intsc"])

#def pldist(self, x1, y1, x2, y2, x, y) :
#	print "x1, y1, x2, y2, x, y", x1, y1, x2, y2, x, y #XXX
#	n0, n1 = -y2+y1, x2-x1
#	den = sqrt((n0**2)+(n1**2))
##	print "xxx:", (x*n0) / den, (y*n1) / den, (x1*n0) / den, (y1*n1) / den
#	dist =  ((x*n0)+(y*n1)+-(x1*n0)-(y1*n1))/den if den else self.ppdist(x1, y1, x, y)

#	#print x-((dist*n0)/den), y-((dist*n1)/den)
#	
#	r = pldist_t(abs(dist), (x-((dist*n0)/den), y-((dist*n1)/den)))
#	return r


if __name__ == "__main__" :

#	print pldist(None,
#		0, 0, 
#		2, 2,
#		0, 1.5)
#	exit(0)

	parser = argparse.ArgumentParser(description="bloced")
	parser.add_argument("file", metavar="fname", type=str, nargs=1,
                   help="file to open")
	args = parser.parse_args()
	be = BlockEditorWindow()
	if args.file :
		be.open_this_file_new(args.file[0])
	be.root.mainloop()

# ------------------------------------------------------------------------------------------------------------

