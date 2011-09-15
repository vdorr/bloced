
from Tkinter import * 
from pprint import pprint
from collections import namedtuple
import autoroute
from tkFileDialog import askopenfilename, asksaveasfilename
import pickle
from sys import exit
from dfs import *
from functools import partial
from math import sqrt
from itertools import ifilter, imap, chain

# ------------------------------------------------------------------------------------------------------------

class Block(Canvas) :

	def onMouseDown(self, event) :
		tw = event.widget.find_overlapping(event.x - 1, event.y - 1, event.x + 1, event.y + 1)
		if not tw or not tw[0] in self.window2term :
			return None
		self.movingObject = self.window2term[tw[0]]
		#if not self.model.can_move :
		#	return None
		self.start = event
		xo, yo = tuple(self.canvas.coords(self.window))
		self.offset = (event.x + xo, event.y + yo)
		self.line = self.canvas.create_line(0, 0, 0, 0, arrow=LAST, arrowshape=(10,10,5))

	def onMouseMove(self, event) :
		if not self.movingObject :
			return None
		xo, yo = tuple(self.canvas.coords(self.window))
		self.canvas.coords(self.line, self.offset[0], self.offset[1],
			event.x + xo, event.y + yo)

	def onMouseUp(self, event) :
		if not self.movingObject :
			return None
		self.start = None
		srcterm = self.movingObject
		self.movingObject = None
		self.canvas.delete(self.line)
		self.line = None
		xo0, yo0, ro0, bo0 = tuple(self.canvas.bbox(self.window))
		dstx = event.x + xo0
		dsty = event.y + yo0
		target = self.canvas.find_overlapping(dstx - 1, dsty - 1, dstx + 1, dsty + 1)
		if not target :
			return None
		blck = self.editor.window_index[target[0]]
		xo1, yo1, ro1, bo1 = tuple(self.canvas.bbox(blck.window))
		tdstx = dstx - xo1
		tdsty = dsty - yo1
		term = blck.find_overlapping(tdstx - 1, tdsty - 1, tdstx + 1, tdsty + 1)
		if term and term[0] in blck.window2term :
			dstterm = blck.window2term[term[0]]
			if blck == self and srcterm == dstterm :
				return None
			if self.editor.model.can_connect(self.model, srcterm, blck.model, dstterm) :
				self.editor.model.add_connection(self.model, srcterm, blck.model, dstterm)

	def onConfigure(self, event) :
	#	# update position of block, notify wires
		#print("updating coords (0)")
		self.model.left, self.model.top, r, b = tuple(self.canvas.bbox(self.window))

	def __init__(self, editor, model) :
		self.editor = editor
		self.canvas = editor.canv
		self.model = model
		
		Canvas.__init__(self, width=self.model.width, height=self.model.height, bg="white",
			borderwidth=0, highlightthickness=0)
		self.window = self.canvas.create_window(self.model.left, self.model.top,
			window=self, anchor=NW)
		self.create_text(0, 0, text=self.model.caption, anchor=NW)
		self.create_rectangle(0, 0, self.model.width - 1, self.model.height - 1)
		
		self.movingObject = None
		self.bind("<B1-Motion>", self.onMouseMoveW)
		self.bind("<ButtonPress-1>", self.onMouseDownW)
		self.bind("<ButtonRelease-1>", self.onMouseUpW)
		self.bind("<Configure>", self.onConfigure)

		tsz = 12
		sides = {
			N : lambda p: (self.model.width*p-tsz/2, 0),
			S : lambda p: (self.model.width*p-tsz/2, self.model.height-tsz),
			W : lambda p: (0, self.model.height*p-tsz/2),
			E : lambda p: (self.model.width-tsz-1, self.model.height*p-tsz/2),
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
		self.tag_bind(o, '<B1-Motion>', self.onMouseMove)
		self.tag_bind(o, '<ButtonPress-1>', self.onMouseDown)
		self.tag_bind(o, '<ButtonRelease-1>', self.onMouseUp)

	def onMouseDownW(self, event) :
		self.start = event
		self.affected_wires = filter(lambda c: self.model in (c[0][0], c[0][2]), #sb, st, tb, tt
			self.editor.connection2line.items())
		for k, v in self.affected_wires :
			self.editor.update_connection(*(k + (False,)))

	def onMouseMoveW(self, event) :
		if not self.movingObject :
			self.canvas.move(self.window, event.x - self.start.x, event.y - self.start.y)
			for k, v in self.affected_wires :
				self.editor.update_connection(*(k + (False,)))

	def onMouseUpW(self, event) :
		self.start = None
		for k, v in self.affected_wires :
			self.editor.update_connection(*(k + (True,)))
		self.affected_wires = None
		#if self.movingObject :
		#	print("updating coords")
		#	self.model.left, self.model.top, r, b = tuple(self.canvas.bbox(self.window))
		#TODO reroute wires

# ------------------------------------------------------------------------------------------------------------

class BlockEditor(Frame, GraphModelListener) :

	# ----------------------------------------------------------------------------------------------------

	def block_added(self, model) :
		b = Block(self, model)
		self.block_index[model] = b
		self.window_index[b.window] = b

	def block_removed(self, block) :
		window = self.block_index[block].window
		self.canv.delete(window)
		self.block_index.pop(block)
		self.window_index.pop(window)

	def block_changed(self, block) :
		pass

	def connection_added(self, sb, st, tb, tt) :
		line = self.canv.create_line(0, 0, 0, 0, arrow=LAST, arrowshape=(10,10,5))
		self.connection2line[(sb, st, tb, tt)] = (line, [])
		self.update_connection(sb, st, tb, tt, True)

	def connection_removed(self, sb, st, tb, tt) :
		self.canv.delete(self.connection2line[(sb, st, tb, tt)][0])

	# ----------------------------------------------------------------------------------------------------
	
	def update_connection(self, sb, st, tb, tt, fullroute) :
		line, path = self.connection2line[(sb, st, tb, tt)]

		s0 = self.get_term_outside_location(sb.left, sb.top, st, sb)
		t0 = self.get_term_outside_location(tb.left, tb.top, tt, tb)

		bump = 16
		bumps = { N: (0, -bump), S: (0, bump), W: (-bump, 0), E: (bump, 0) }

		bump0x, bump0y = bumps[st.side]
		s = autoroute.pnt(s0[0] + bump0x, s0[1] + bump0y)

		bump1x, bump1y = bumps[tt.side]
		t = autoroute.pnt(t0[0] + bump1x, t0[1] + bump1y)

		route = None
		if fullroute :
			r1 = autoroute.rct(sb.left, sb.top, sb.width, sb.height)
			r2 = autoroute.rct(tb.left, tb.top, tb.width, tb.height)
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

	line_edit_data = namedtuple("line_edit_data", ["x"])

	def pldist(self, x1, y1, x2, y2, x, y) :
		n0, n1 = -y2+y1, x2-x1
		return abs((x*n0)+(y*n1)+-(x1*n0)-(y1*n1))/sqrt((n0**2)+(n1**2))

	def ppdist(self, x1, y1, x2, y2) :
		return sqrt((x1-x2)**2+(y1-y2)**2)

	def default_mousedown(self, event) :
		self.manipulating = False
		ssz = 4
		o = self.canv.find_overlapping(
			event.x - ssz, event.y - ssz, event.x + ssz, event.y + ssz)
		if o :
			item = filter(lambda v: o[0] == v[1][0], self.connection2line.items())
			if item :
				#print item
				self.manipulating = "connection"
				self.mdata = item[0]
				
				route = item[0][1][1]
				
				kneebonus = 4
				
				indices = xrange(0, len(route)-2, 2)
				dist = chain(
					imap(lambda i: ((i, 2), self.pldist(
					route[i], route[i+1], route[i+2], route[i+3], event.x, event.y)),
					indices),
					imap(lambda i: ((i, 1), self.ppdist(
					route[i], route[i+1], event.x, event.y) - kneebonus),
					indices))
				self.mdata2 = reduce(lambda a,b: a if a[1] < b[1] else b, dist)[0]
				print "self.mdata2", self.mdata2
				self.move_start = event

	def default_mousemove(self, event) :
		if self.manipulating == "connection" :
			diffX, diffY = (event.x - self.move_start.x), (event.y - self.move_start.y)
			self.move_start = event
			
			for i in xrange(self.mdata2[0], self.mdata2[0]+(self.mdata2[1]*2), 2) :
				if i > 0 and (i+2)<len(self.mdata[1][1]) :
					self.mdata[1][1][i] += diffX
					self.mdata[1][1][i+1] += diffY

			#self.connection2line[(sb, st, tb, tt)] = (line, linecoords)
			self.canv.coords(self.mdata[1][0], *self.mdata[1][1])

	def default_mouseup(self, event) :
		self.manipulating = None
		self.mdata = None
		self.mdata2 = None

	# ----------------------------------------------------------------------------------------------------

	def paste_block_on_mouse_down(self, prototype, event) :
		b = BlockModel(prototype.get_type_name(), event.x, event.y, 64, 64,
			prototype.get_terms())
		self.model.add_block(b)
		self.canv.bind("<ButtonPress-1>", self.default_mousedown)

	# ----------------------------------------------------------------------------------------------------

	def __init__(self, parent) :
	
		Frame.__init__(self, parent)

		self.grid(column=0, row=0, sticky=(N, W, E, S))

		self.canvas_scrollregion = (0, 0, 2048, 2048)
		self.canv = Canvas(self, scrollregion=self.canvas_scrollregion, bg="white")
		self.canv.grid(column=0, row=0, sticky=(W, E, N, S))
		self.canv.columnconfigure(0, weight=1)
		self.canv.rowconfigure(0, weight=1)
		#self.canv.bind("<Motion>", lambda event: pprint((event.x, event.y)))

		yscroll = Scrollbar(self, orient=VERTICAL, command=self.canv.yview)
		yscroll.grid(column=1, row=0, sticky=(N,S))
		self.canv.configure(yscrollcommand=yscroll.set)

		xscroll = Scrollbar(self, orient=HORIZONTAL, command=self.canv.xview)
		xscroll.grid(column=0, row=1, sticky=(W,E))
		self.canv.configure(xscrollcommand=xscroll.set)
		
		self.canv.bind("<ButtonPress-1>", self.default_mousedown)
		self.canv.bind("<B1-Motion>", self.default_mousemove)
		self.canv.bind("<ButtonRelease-1>", self.default_mouseup)

		self.block_index = {}
		self.window_index = {}
		self.model = None
		self.connection2line = {}

# ------------------------------------------------------------------------------------------------------------

class BlockEditorWindow :

	def save_file(self) :
		fname = asksaveasfilename()
		if fname :
			try :
				f = open(fname, "wb")
				mdl = self.bloced.get_model()
				self.bloced.set_model(None)
				pickle.dump(mdl, f)
				self.bloced.set_model(mdl)
				f.close()
			except IOError :
				print("IOError")
			except pickle.PickleError :
				print("PickleError")
				raise

	def open_file(self) :
		fname = askopenfilename()
		if fname :
			try :
				f = open(fname, "rb")
				mdl = pickle.load(f)
				f.close()
				self.bloced.set_model(mdl)
			except IOError :
				print("IOError")
			except pickle.PickleError :
				print("PickleError")
	
	def begin_paste_block(self, prototype) :
		#print prototype.get_type_name()
		#return None
		self.bloced.canv.bind("<ButtonPress-1>",
			partial(self.bloced.paste_block_on_mouse_down, prototype))

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

		menubar = Menu(self.root)
		self.root["menu"] = menubar
		menu_file = Menu(menubar)
		menubar.add_cascade(menu=menu_file, label="File")
		menu_file.add_command(label="New", command=lambda: pprint("newFile"))
		menu_file.add_command(label="Open...", command=self.open_file)
		menu_file.add_command(label="Save As...", command=self.save_file)
		menu_file.add_separator()
		menu_file.add_command(label="Export...", command=None)
		menu_file.add_separator()
		menu_file.add_command(label="Quit", command=lambda: self.root.destroy())

		self.bloced = BlockEditor(mainframe)
		self.bloced.grid(column=0, row=1, sticky=(W, E, N, S))
		self.bloced.columnconfigure(0, weight=1)
		self.bloced.rowconfigure(0, weight=1)

		model = GraphModel()
		self.bloced.set_model(model)
				
		#b0 = BlockModel("0th", 300, 300, 64, 64,
		#	[ In("a", W, 0.5), Out("b", E, 0.5) ])
		#model.add_block(b0)
		#b1 = BlockModel("1st", 100, 100, 64, 64,
		#	[ In("a", W, 0.5), Out("b", E, 0.5) ])
		#model.add_block(b1)

		mnuDbg = Menu(menubar)
		menubar.add_cascade(menu=mnuDbg, label="Debug")
		mnuDbg.add_command(label="try remove",
			command = lambda: m.remove_block(b1))

		self.blockfactory = create_block_factory()

		menu_blocks = Menu(menubar)
		menubar.add_cascade(menu=menu_blocks, label="Blocks")
		for bp in self.blockfactory.get_block_list() :
			menu_blocks.add_command(label =  bp.get_type_name(),
				command = partial(self.begin_paste_block, bp))

# ------------------------------------------------------------------------------------------------------------

if __name__ == "__main__" :

	be = BlockEditorWindow()
	be.root.mainloop()

# ------------------------------------------------------------------------------------------------------------

