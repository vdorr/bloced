#! /usr/bin/python

from sys import exit, version_info
from pprint import pprint
from collections import namedtuple
from functools import partial
from itertools import dropwhile, groupby
#import argparse #TODO use sys instead
import traceback
import os
import string
import pickle
import fnmatch

import pyperclip

import webbrowser

import autoroute
from dfs import *
import core
from serializer import *
#from implement import implement_dfs, try_mkmac, here
from utils import here
import mathutils
import build

if version_info.major == 3 :
	from tkinter import * #TODO this is not good
	from tkinter import font as tkFont #XXX ?!?!?!?
	import tkinter.messagebox as tkMessageBox
	from tkinter.filedialog import askopenfilename, asksaveasfilename
	from tkinter import ttk
	from tkinter.simpledialog import Dialog
	from configparser import SafeConfigParser
else :
	from Tkinter import * #TODO this is not good
	import tkFont
	import tkMessageBox
	from tkFileDialog import askopenfilename, asksaveasfilename
	import ttk
	from tkSimpleDialog import Dialog
	from ConfigParser import SafeConfigParser

# ------------------------------------------------------------------------------------------------------------

#TODO map from model to presentation: { dfs.JointProto : Joint, BlockModel:
#TODO somehow implement system of "actions" so its not neccessary to have separate  implementations
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


def get_basic_mod_keys(state) :
	return state & ~(BIT_CAPSLOCK | BIT_NUMLOCK)


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
	UNSAVED_DATA_WILL_BE_LOST = "Unsaved data will be lost"
	APP_INFO = os.linesep.join((APP_NAME, "graphical programming toy"))
	HELP_URL = "http://www.tinfoilhat.cz"
	POLL_WORKERS_PERIOD = 1000
	SHEET_NAME_SEED = "Sheet{0}"

cfg = Configuration()

# ------------------------------------------------------------------------------------------------------------

class UserSettings(object) :

	def set_defaults(self) :
		self.main_width = 800
		self.main_height = 600
		self.main_left = 127
		self.main_top = 127
		self.recent_files = []

	def __init__(self) :
		self.set_defaults()

# ------------------------------------------------------------------------------------------------------------

selection_t = namedtuple("snt", [ "blocks", "lines" ])#, "joints" ]);
event_t = namedtuple("event_t", ["x", "y", "state"])

# ------------------------------------------------------------------------------------------------------------

class MenuItem(object) :
	def __init__(self) :
		self.text = None
		self.accel = None
		self.handler = None

class SepMnu(MenuItem) :
	pass


class RadioMnu(MenuItem) :
	def __init__(self, text, accel, handler, value=None, selected=False) :
		super(RadioMnu, self).__init__()
		self.text, self.accel, self.handler, self.value, self.selected = text, accel, handler, value, selected


class CheckMnu(MenuItem) :
	def __init__(self, text, accel, handler, value=None, selected=False) :
		super(CheckMnu, self).__init__()
		self.text, self.accel, self.handler, self.value, self.selected = text, accel, handler, selected


class CmdMnu(MenuItem) :
	def __init__(self, text, accel, handler) :
		super(CmdMnu, self).__init__()
		self.text, self.accel, self.handler = text, accel, handler


class CascadeMnu(MenuItem) :
	def __init__(self, text, items) :
		super(CascadeMnu, self).__init__()
		self.text, self.items = text, items


# ------------------------------------------------------------------------------------------------------------

#class textbox(Frame):

#	def __init__(self, parent, msg) :
#		Frame.__init__(self,parent)
#		self.g_label = Label(self,text=msg)
#		self.g_label.pack(side=LEFT,expand=False)
#		self.g_entry = Entry(self)
#		self.g_entry.pack(side=LEFT, fill=X, expand=True)
#		self.pack(fill=X, anchor=NW, expand=True)

#	def text(self) :
#		return self.gui["entry"].get()

# ------------------------------------------------------------------------------------------------------------

class InputDialog(Dialog) :


	def __init__(self, parent, text="", initial="", items=None) :
#		self.__text = text
#		self.__initial_value = initial
		self.__items = items if items else [ (text, initial) ]
		self.__one_value = not items
		Dialog.__init__(self, parent)


	def body(self, master):
		self.__entries = []
#		self.value = (None, ) * len(self.__items)
		self.value = None
		for (text, initial), row in zip(self.__items, count()) :
			Label(master, text=text+" ").grid(row=row)
			e1 = Entry(master)
			e1.insert(0, str(initial))
			e1.grid(row=row, column=1)
			self.__entries.append(e1)
			
		return self.__entries[0]


	def apply(self):
		if self.__one_value :
			self.value = self.__entries[0].get()
		else :
			self.value = tuple(e1.get() for e1 in self.__entries)

# ------------------------------------------------------------------------------------------------------------

class CustomDialog(Toplevel):

	"""
	taken from http://effbot.org/tkinterbook/tkinter-dialog-windows.htm
	"""

	def __init__(self, parent, title = None) :
		Toplevel.__init__(self, parent)
		self.transient(parent)
		if title:
			self.title(title)
		self.parent = parent
		self.result = None
		body = Frame(self)
		self.initial_focus = self.body(body)
		body.pack(padx=5, pady=5)
		self.buttonbox()
#		self.grab_set()
		if not self.initial_focus:
			self.initial_focus = self
		self.protocol("WM_DELETE_WINDOW", self.cancel)
		self.geometry("+%d+%d" % (parent.winfo_rootx()+50, parent.winfo_rooty()+50))
		self.initial_focus.focus_set()
		self.wait_window(self)


	def body(self, master) :
		# create dialog body.  return widget that should have
		# initial focus.  this method should be overridden
		pass


	def buttonbox(self) :
		# add standard button box. override if you don't want the
		# standard buttons
		box = Frame(self)
		w = Button(box, text="OK", width=10, command=self.ok, default=ACTIVE)
		w.pack(side=LEFT, padx=5, pady=5)
		w = Button(box, text="Cancel", width=10, command=self.cancel)
		w.pack(side=LEFT, padx=5, pady=5)
		self.bind("<Return>", self.ok)
		self.bind("<Escape>", self.cancel)
		box.pack()


	def ok(self, event=None) :
		if event and event.state & BIT_CONTROL :
			return
		if not self.validate() :
			self.initial_focus.focus_set() # put focus back
			return
		self.withdraw()
		self.update_idletasks()
		self.apply()
		self.cancel()


	def cancel(self, event=None) :
		# put focus back to the parent window
		self.parent.focus_set()
		self.destroy()


	def validate(self) :
		return 1 # override


	def apply(self) :
		pass # override


class TextEditorDialog(CustomDialog) :


	def __init__(self, parent, initial) :
		self.value = initial
		CustomDialog.__init__(self, parent)


	def body(self, master) :
		txt = Text(master, wrap="none")
		self.txt = txt
		txt.insert("1.0", self.value)
		self.txt.grid(column=1, row=1, sticky=(W, E, N, S))
		yscroll = Scrollbar(master, orient=VERTICAL, command=self.txt.yview)
		yscroll.grid(column=2, row=1, sticky=(N,S))
		self.txt.configure(yscrollcommand=yscroll.set)
		xscroll = Scrollbar(master, orient=HORIZONTAL, command=self.txt.xview)
		xscroll.grid(column=1, row=2, sticky=(W,E))
		self.txt.configure(xscrollcommand=xscroll.set)
		return txt


	def apply(self):
		self.value = self.txt.get("1.0", "end")


# ------------------------------------------------------------------------------------------------------------

class BlockBase(object) :

	def get_wires(self, sel_blocks=None) :
		sel_blocks = sel_blocks if sel_blocks else (self, )
		return [ ((b0, t0, b1, t1), data) for (b0, t0, b1, t1), data in self.editor.connection2line.items()
			if all([ blck.model in (b0, b1) for blck in sel_blocks ]) ]

	def bind_as_term(self, o) :
		self.tag_bind(o, "<B1-Motion>", self.term_onMouseMove)#TODO use partial(
		self.tag_bind(o, "<ButtonPress-1>", self.term_onMouseDown)
		self.tag_bind(o, "<ButtonRelease-1>", self.term_onMouseUp)


# ------------------------------------------------------------------------------------------------------------

if 0 :
	from PIL import ImageTk, Image, ImageDraw, ImageFont

	class ImageLabel(object) :

		def __init__(self, parent_block, name, text, pos, font) :
			if not hasattr(ImageLabel, "font") :
				ImageLabel.font = ImageFont.load_default()
				_, ImageLabel.txt_height = ImageLabel.font.getsize("jJ")
			fnt = ImageLabel.font
			size = fnt.getsize(text)
			im = Image.new("RGBA", size, (0, 0, 0, 0))
			draw = ImageDraw.Draw(im)
			flipv, fliph, rot = parent_block.model.orientation
			if name == "caption_lbl" :
				lbl_x, lbl_y = parent_block.model.get_label_pos(*size)
				pos = lbl_x, lbl_y
			else :
				lbl_x, lbl_y = pos
			draw.text((0, 0), text, font=fnt, fill=(0, 0, 0)) #Draw text
			img = ImageTk.PhotoImage(
				im if not parent_block.model.orientation[2] % 180 else im.rotate(90, expand=True))
			i = parent_block.create_image((lbl_x, lbl_y), image=img, anchor=NW)
			self.__data = (img, text, pos, i)
			self.canvas_item = i
			self.text = text
			self.pos = pos

else :

	class ImageLabel(object) :

		def __init__(self, parent_block, name, text, pos, font) :
			txt_width = parent_block.editor.font.measure(text)
			size = (txt_width, parent_block.editor.txt_height)
			flipv, fliph, rot = parent_block.model.orientation
			if name == "caption_lbl" :
				lbl_x, lbl_y = parent_block.model.get_label_pos(*size)
				pos = lbl_x, lbl_y
			else :
				lbl_x, lbl_y = pos
			i = parent_block.create_text((lbl_x, lbl_y), text=text, anchor=NW,
				font=font)
			self.__data = (None, text, pos, i)
			self.canvas_item = i
			self.text = text
			self.pos = pos


class Block(Canvas, BlockBase) :


	def term_onMouseDown(self, e) :
		self.term_hit = True
		self.editor.clear_selection()
		return self.editor.blckMouseDown(self, e)


	def term_onMouseMove(self, e) :
		return self.editor.blckMouseMove(self, e)


	def term_onMouseUp(self, e) :
		self.term_hit = False
		return self.editor.blckMouseUp(self, e)


#	editables = (core.ConstProto, core.DelayProto, core.TapProto, core.TapEndProto,
#		core.InputProto, core.OutputProto)


	def autosize_to_text(self) :
		lines = self.model.value[0].split(os.linesep)
		margin = self.editor.font.measure("x")
		w = max(self.editor.font.measure(l) for l in lines) + margin
		h = (self.editor.font.metrics("linespace") * len(lines)) + margin
		self.model.width = w
		self.model.height = h


	#TODO class EditableBlock(Block) :
	def onDblClick(self, e) :
#		if type(self.model.prototype) in Block.editables :
#		print here()#, self.model.prototype, self.model.prototype.values
		self.__dbl_click = True
		if core.compare_proto_to_type(self.model.prototype, core.TextAreaProto) :
			d = TextEditorDialog(self, self.model.value[0])
			if d.value :
				self.editor.model.begin_edit()
				self.model.value = d.value.strip()
				self.autosize_to_text()
				self.editor.model.end_edit()
		elif self.model.prototype.values :
			items = [ (name, val) for (name, _), val
				in zip(self.model.prototype.values, self.model.value)]
			d = InputDialog(self, items=items)
			if d.value :
				self.editor.model.begin_edit()
				self.model.value = d.value
				self.editor.model.end_edit()
				self.update_text()
#			entry = Entry(self)
#			entry.insert(0, str(self.model.value))
#			w = self.create_window(0, 0, window=entry, anchor=NW)
#			entry.bind("<Return>", lambda e: self.close_editor(True, w, entry))
#			entry.bind("<Escape>", lambda e: self.close_editor(False, w, entry))
#			entry.bind("<FocusOut>", lambda e: self.close_editor(False, w, entry))
#			entry.pack(side=LEFT, fill=X)
#			entry.focus()

#	def close_editor(self, accept, w, entry) :
#		if accept :
#			self.model.value = str(entry.get())
#			self.update_text()
#		self.delete(w)
#		entry.destroy()
#		self.config(width=self.model.width, height=self.model.height, bg="white",
#			borderwidth=0, highlightthickness=0)


	def update_text(self) :
		self.__update_label("caption_lbl", self.__caption_lbl_pos, self.model.presentation_text)


	def select_next(self) :
		self.editor.select_next()


	def __update_label(self, name, pos, text) :
		if name in self.__labels :
			l = self.__labels[name]
			if l.text == text and l.pos == pos :
				return l.canvas_item
			else :
				self.__labels.pop(name)
				self.delete(l.canvas_item)
		lbl = ImageLabel(self, name, text, pos, self.editor.font)
		self.__labels[name] = lbl
		return lbl.canvas_item


	def popup(self, e) :
		self.editor.ui.editor_popup.tk_popup(e.x_root, e.y_root, 0)


	def __init__(self, editor, model) :
		self.editor = editor
		self.canvas = editor.canv
		self.model = model
		self.__labels = {}
		self.mouse_down_at = None
		self.__dbl_click = False

		Canvas.__init__(self, self.editor.canv,
			width=self.model.width, height=self.model.height,
			bg="white", borderwidth=0, highlightthickness=0)

		self.window = self.canvas.create_window(self.model.left, self.model.top,
			window=self, anchor=NW)
		
		self.bind("<B1-Motion>", self.onMouseMoveW)
		self.bind("<ButtonPress-1>", self.onMouseDownW)
		self.bind("<ButtonRelease-1>", self.onMouseUpW)
#		self.bind("<Configure>", self.onConfigure)
		self.bind("<Double-Button-1>", self.onDblClick)
		self.bind("<Tab>", lambda a: self.select_next())
		self.bind("<ButtonPress-3>", self.popup)

		self.border_rect = self.create_rectangle(0, 0, self.model.width - 1, self.model.height - 1)

#		self.caption_txt = self.create_text(0, 0, anchor=NW)
#		self.__caption_lbl_pos = property(lambda self: )
		self.__caption_lbl_pos = (2, 1)
#		print "self.model.presentation_text=", self.model.presentation_text
		self.__caption_lbl = self.__update_label("caption_lbl", self.__caption_lbl_pos, "")

#		self.update_text()
		
		self.movingObject = None
		self.affected_wires = None
		self.window2term = {}
		self.__term2txt = {}
		self.term_hit = False

		self.create_terms = True
		self.reshape()


	def reshape(self) :
		self.window2term.clear()
		self.__term2txt.clear()
		self.regenerate_terms()
		self.coords(self.border_rect, 0, 0, self.model.width-1, self.model.height-1)
		self.canvas.coords(self.window, self.model.left, self.model.top)
		self.canvas.itemconfig(self.window, width=self.model.width, height=self.model.height)
#		for k, v in self.get_wires() :
#			self.editor.update_connection(*(k + (True,)))
		self.update_text()


	def regenerate_terms(self) :

		txt_height = self.editor.txt_height

		for t in self.model.terms :
			self.delete(t.name)

		if not self.create_terms :
			return None

		for t, nr in self.model.get_terms_flat() :

			term_tag = t.name
			term_label = self.model.get_term_presentation_text(t, nr)

			t_side = self.model.get_term_side(t)

#XXX XXX XXX
#			fnt = self.editor.font_h if t_side in (W, E) else self.editor.font_v
#			txt_width = fnt.measure(term_label)
#			txt_width, _ = self.editor.font.getsize(term_label)
			txt_width = self.editor.font.measure(term_label)
#XXX XXX XXX

			(x, y), (txtx, txty) = self.model.get_term_and_lbl_pos(t, nr, txt_width, txt_height)
			poly = get_term_poly(
				x,#x-(term_size if t_side == E else 0),
				y,#y-(term_size if t_side == S else 0),
				txt_height, self.model.get_term_side(t), t.direction, txt_width)

			w = self.create_polygon(*poly, fill="white", outline="black", tags=term_tag)
			self.bind_as_term(w)

			txt = self.create_text(txtx, txty, text=term_label, anchor=NW,
				fill="black", tags=term_tag, font=self.editor.font)
			self.bind_as_term(txt)

			self.window2term[w] = t
			self.__term2txt[t] = txt


	def onMouseDownW(self, e) :
		if self.term_hit :
			return None
		self.mouse_down_at = self.move_start = (e.x_root, e.y_root)
#		if e.state & BIT_SHIFT : #TODO
#			pass
		if self.editor.selection and self in self.editor.selection.blocks :
			sel_blocks = tuple(self.editor.selection.blocks)
		else :
			sel_blocks = (self, )
			self.editor.create_selection_from_list(sel_blocks, [])
		self.editor.model.begin_edit()
		self.affected_wires = self.get_wires(sel_blocks=sel_blocks)


	def onMouseMoveW(self, e) :
		if self.term_hit :
			return None
#		if not self.movingObject and self.start : # TODO move to editor
		if not self.movingObject and self.move_start : # TODO move to editor
			self.editor.move_selection(e.x_root-self.move_start[0], e.y_root-self.move_start[1],
				editing_begin_edit_only=True)
			self.move_start = (e.x_root, e.y_root)

	def onMouseUpW(self, e) :
		if self.term_hit :
			return None
		need_wire_update = self.mouse_down_at != (e.x_root, e.y_root)
		self.mouse_down_at = self.move_start = None
		if self.affected_wires and need_wire_update :
			for k, v in self.affected_wires :
				self.editor.update_connection(*(k + (True,)))
		self.affected_wires = None
		if self.__dbl_click :
			self.__dbl_click = False
		else :
			self.editor.model.end_edit()


# ------------------------------------------------------------------------------------------------------------

class Joint(Block) :
	def __init__(self, *u, **v) :
		super(Joint, self).__init__(*u, **v)
		self.create_terms = False
		self.reshape()
		self.configure(bg="black")

# ------------------------------------------------------------------------------------------------------------

class BlockEditor(Frame, GraphModelListener) :

	def editing(f):
		def decorated(*v, **w) :
			if "editing_begin_edit_only" in w :
				w.pop("editing_begin_edit_only")
#			print here(10)
			v[0].model.begin_edit()
			y = f(*v, **w)
			if "editing_end_edit_only" in w :
				w.pop("editing_end_edit_only")
			v[0].model.end_edit()
			return y
		return decorated

	# ----------------------------------------------------------------------------------------------------

#TODO move layout functions to model
	def layout_reroute(self) :
		if not self.selection :
			return None

		self.model.begin_edit()
		for block in self.selection.blocks :
			for k, _ in block.get_wires() :
				self.update_connection(*(k + (True,)))
		self.model.end_edit()
		self.resize_selection()


	def equal_spacing(self, axis) :
		if not self.selection or len(self.selection.blocks) < 3 :
			return None

		if axis == "x" :
			get_coord = lambda block: (block.model.left, block.model.width)
			set_coord = lambda block, a: block.model._BlockModel__set_left(a)
		elif axis == "y" :
			get_coord = lambda block: (block.model.top, block.model.height)
			set_coord = lambda block, a: block.model._BlockModel__set_top(a)
		else :
			raise Exception("unknown spacing")

		blocks = tuple(sorted(((b, get_coord(b)) for b in self.selection.blocks),
			key=lambda b: b[1][0]))

		min_a = min(a for b, (a, _) in blocks)
		max_a = max(sum(a_sz) for b, a_sz in blocks)
		blocks_size = sum(size for b, (_, size) in blocks)
		spacing = (max_a - min_a - blocks_size) / (len(blocks) - 1)

		self.model.begin_edit()
		v = min_a
		for block, (a, size) in blocks :
			set_coord(block, v)
			v += size + spacing
		self.model.end_edit()
		self.resize_selection()


	def layout_align(self, align) :
		if not self.selection :
			return None

		if align == "lefts" :
			f_scan = lambda blocks : min(b.left for b in blocks)
			f_xfrm = lambda l, b : (l, b.top)
		elif align == "centers" :
			f_scan = lambda blocks : sum((b.left+b.width/2) for b in blocks) / len(blocks)
			f_xfrm = lambda c, b : (c - b.width / 2, b.top)
		elif align == "rights" :
			f_scan = lambda blocks : max((b.left+b.width) for b in blocks)
			f_xfrm = lambda r, b : (r-b.width, b.top)
		elif align == "tops" :
			f_scan = lambda blocks : min(b.top for b in blocks)
			f_xfrm = lambda t, b : (b.left, t)
		elif align == "middles" :
			f_scan = lambda blocks : sum((b.top+b.height/2) for b in blocks) / len(blocks)
			f_xfrm = lambda c, b : (b.left, c - b.height / 2)
		elif align == "bottoms" :
			f_scan = lambda blocks : max((b.top+b.height) for b in blocks)
			f_xfrm = lambda t, b : (b.left, t-b.height)
		else :
			raise Exception("unknown alignment")

		p = f_scan(tuple(block.model for block in self.selection.blocks))
		self.model.begin_edit()
		for block in self.selection.blocks :
			block.model.left, block.model.top = f_xfrm(p, block.model)
		self.model.end_edit()
		self.resize_selection()


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
		dstx = e.x + xo
		dsty = e.y + yo
#		tblock, _ = self.__get_obj_at(dstx, dsty)
		block, term = self.__get_term_at(sender, dstx, dsty)
		self.model.begin_edit()
		if term :
			p = (block.model, term)
			conn = [ (src, dst) for src, dst in self.model.connections.items()
				if p == src or p in dst ]
			if conn :
				((sb, st), ((tb, tt),)), = conn
#				assert(len(dst) == 1)
#				print "term connected", sb, st, tb, tt
				self.model.remove_connection(sb, st, tb, tt)

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


	def __get_term_at(self, blck, dstx, dsty, filt_dir=None) :
		xo1, yo1, ro1, bo1 = tuple(self.canv.bbox(blck.window))
		tdstx, tdsty = dstx - xo1, dsty - yo1
		if not core.compare_proto_to_type(blck.model.prototype, core.JointProto) :
			terms = blck.find_overlapping(tdstx-1, tdsty-1, tdstx+1, tdsty+1)
			dstterms = [ blck.window2term[t] for t in terms if t in blck.window2term ]
		else :
			dstterms = blck.model.terms
#		print "__get_term_at:", [(t, t.direction, t.direction ==filt_dir) for t in dstterms]
#		dstterm = None
#		if terms and terms[0] in blck.window2term :
#			dstterm = blck.window2term[terms[0]]
		f_dstterms = [ t for t in dstterms if (filt_dir == None or t.direction == filt_dir) ]
		return (blck, f_dstterms[0] if f_dstterms else None)


	def __get_obj_at(self, dstx, dsty, filt_dir=None) :
		a = 2
		hits = self.canv.find_overlapping(dstx-a, dsty-a, dstx+a, dsty+a)
		hit_blocks = [ self.__get_term_at(self.window_index[w], dstx, dsty, filt_dir)
				for w in hits if w in self.window_index ]
		hit_wires = [ conn for conn, (w, etc) in self.connection2line.items() if w in hits ]
#		pprint(self.window_index)
#		print(hits)
#		print "__get_obj_at: b:", hit_blocks, " w:", hit_wires
		return ( hit_blocks[0] if hit_blocks else None, hit_wires[0] if hit_wires else None)


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

		tblock, twire = self.__get_obj_at(dstx, dsty,
			core.INPUT_TERM if srcterm.direction == core.OUTPUT_TERM else core.OUTPUT_TERM)

		if tblock :
#			print "blckMouseUp:", tblock
			blck, dstterm = tblock
#			if isinstance(blck.model.prototype, core.JointProto) :
#				print "kvak", blck, blck.model, blck.model.terms, dstterm
#				dstterm = Out(0, "", C, 0) if srcterm.direction == core.INPUT_TERM else In(0, "", C, 0)
#				blck.model.terms.append(dstterm)
#				self.canv.tag_raise(blck.window)
#			print "kvak2", sender.model, srcterm, blck.model, dstterm
			if ( dstterm != None and blck != sender and srcterm != dstterm and
					self.model.can_connect(sender.model, srcterm, blck.model, dstterm) ) :
				self.model.add_connection(sender.model, srcterm, blck.model, dstterm, {})
#				self.model.end_edit()
#			else :
#				self.model.end_edit()
#		else :
#			self.model.end_edit()
		elif twire and srcterm.direction == core.INPUT_TERM :
			self.model.begin_edit()
			src_blck, src_term, dst_blck, dst_term = twire
			self.model.remove_connection(src_blck, src_term, dst_blck, dst_term)
			proto = core.JointProto()
			w, h = proto.default_size
			joint = BlockModel(proto, self.model, left=dstx-w/2, top=dsty-h/2)
			self.model.add_block(joint)
			t_in = [ t for t in joint.terms if t.direction == core.INPUT_TERM ][0]
			t_out = [ t for t in joint.terms if t.direction == core.OUTPUT_TERM ][0]
			self.model.add_connection(src_blck,
				src_term[0] if isinstance(src_term, tuple) else src_term, joint, t_in, {})
			self.model.add_connection(joint, t_out, dst_blck,
				dst_term[0] if isinstance(dst_term, tuple) else dst_term, {})
			self.model.add_connection(joint, t_out, sender.model, srcterm, {})
			self.model.end_edit()

	# ----------------------------------------------------------------------------------------------------

	def block_added(self, model) :
	#TODO unify
#		b = self.m_view_types[model.prototype](self, model)
		if core.compare_proto_to_type(model.prototype, core.JointProto) :
			b = Joint(self, model)
		else :
			b = Block(self, model)
			if core.compare_proto_to_type(model.prototype, core.TextAreaProto) :
				self.model.begin_edit()
				b.autosize_to_text()
				self.model.end_edit()
				b.reshape()
		self.block_index[model] = b
		self.window_index[b.window] = b

	def block_removed(self, block) :
		window = self.block_index[block].window
		self.canv.delete(window)
		self.block_index.pop(block)
		self.window_index.pop(window)

	def block_changed(self, block, event=None, reroute=False) :
		if not block in self.block_index :
			return None
		b = self.block_index[block]
		if self.manipulating == None : # and not self.move_indication :
#			traceback.print_stack()
			if event and event["p"] in [ "left", "top", "width", "height",
			  "orientation", "term_meta" ] : # and
				b.reshape()
				do_reroute = reroute #or event["p"] == "term_meta"
				for k, v in b.get_wires() : #XXX move to reshape?
					self.update_connection(*(k + (do_reroute,)))
				if self.selection :
					self.resize_selection()
#			elif event and event["p"] == "term_meta" :
#				print "term_meta changed", event
		b.update_text()

#		if block in self.block_index :
#			print "block_changed: rewiring"
#			for k, v in self.block_index[block].get_wires() :
#				self.update_connection(*(k + (True,)))

	def connection_changed(self, sb, st, tb, tt) :
		line, linecoords = self.connection2line[(sb, st, tb, tt)]
		meta = self.model.get_connection_meta(sb, st, tb, tt)
		if "path" in meta :
			path = meta["path"]
			self.connection2line[(sb, st, tb, tt)] = (line, path)
			self.canv.coords(line, *path)

	def connection_added(self, sb, st, tb, tt, deserializing=False) :
		#TODO i/o arrow dir, make it cleaner
		line = self.canv.create_line(0, 0, 0, 0, arrow=LAST, arrowshape=(10,10,5))
		self.connection2line[(sb, st, tb, tt)] = (line, [])

		conn_meta = dict(self.model.get_connection_meta(sb, st, tb, tt))
#		print(here(), sb, st, tb, tt, "deserializing:", deserializing, "path" in conn_meta)

		if deserializing or "path" in conn_meta :
			if "path" in conn_meta :
				linecoords = list(conn_meta["path"])
				self.connection2line[(sb, st, tb, tt)] = (line, linecoords)
				self.canv.coords(line, *linecoords)
			else :
				self.update_connection(sb, st, tb, tt, True)
		else :
#			self.update_connection(sb, st, tb, tt, True)
			for block in (sb, tb) :
				if block in self.block_index :
					for k, v in self.block_index[block].get_wires() :
						self.update_connection(*(k + (True,)))

#	def rewire_after_conn_changed(self, sb, st, tb, tt) :
#		for b, t in ((sb, st), (tb, tt)) :
#			if isinstance(t, tuple) :
#				for k, v in self.block_index[b].get_wires() :
#					self.update_connection(*(k + (True,)))

	def connection_removed(self, sb, st, tb, tt) :
		for block, term in ((sb, st), (tb, tt)) :
#			if isinstance(block.prototype, core.JointProto) :
#				block.terms.remove(term)
#				if not block.terms and block in self.model.blocks :
#					self.model.remove_block(block)
#			else :
			bm = self.block_index[block]
			bm.reshape()
#			if isinstance(term, tuple) :
#				for k, v in bm.get_wires() :
#					self.update_connection(*(k + (True,)))
#		self.rewire_after_conn_changed(sb, st, tb, tt)
		self.canv.delete(self.connection2line[(sb, st, tb, tt)][0])
		self.connection2line.pop((sb, st, tb, tt))
		for block in (sb, tb) :
			if block in self.block_index :
				for k, v in self.block_index[block].get_wires() :
					self.update_connection(*(k + (True,)))

	# ----------------------------------------------------------------------------------------------------
	
	def update_connection(self, sb, t0, tb, t1, fullroute) :
#		print(here(), fullroute)
		line, path = self.connection2line[(sb, t0, tb, t1)]

		st, sn = t0 if isinstance(t0, tuple) else (t0, 0)
		tt, tn = t1 if isinstance(t1, tuple) else (t1, 0)

#		print "update_connection: ", sb, st, sn, tb, tt, tn, line, path

#		txt_height = self.txt_height
#			txt_width = self.editor.font.measure(sb.get_term_presentation_text(st, sn))

		s0 = sb.get_term_location(st, sn,
			self.font.measure(sb.get_term_presentation_text(st, sn)), self.txt_height)
		tA = tb.get_term_location(tt, tn,
			self.font.measure(tb.get_term_presentation_text(tt, tn)), self.txt_height)

#		print "update_connection: tt, tn, tA =", tt, tn, tA, (tb.left, tb.width)

		bump = cfg.BLOCK_WIRE_STUB
		bumps = { N: (0, -bump), S: (0, bump), W: (-bump, 0), E: (bump, 0), C: (0, 0) }

		bump0x, bump0y = bumps[sb.get_term_side(st)]
		s = autoroute.pnt(int(s0[0]+bump0x), int(s0[1]+bump0y))

		bump1x, bump1y = bumps[tb.get_term_side(tt)]
		t = autoroute.pnt(int(tA[0]+bump1x), int(tA[1]+bump1y))

		route = None
		if fullroute :
			r1 = (autoroute.rct(sb.left, sb.top, sb.width, sb.height) if sb.get_term_side(st) != C
				else autoroute.rct(sb.left, sb.top, 1, 1))
			r2 = (autoroute.rct(tb.left, tb.top, tb.width, tb.height) if tb.get_term_side(tt) != C
				else autoroute.rct(tb.left, tb.top, 1, 1))
			bbox = autoroute.choose_bbox(r1, r2,
				autoroute.rct(*self.canvas_scrollregion), bump + 1)
			route = autoroute.mtroute_simple(s, t, bbox, r1, r2)

		if route :
			linecoords = reduce(lambda w, p: w + [ p[0], p[1] ],
				route, list(s0)) + [ tA[0], tA[1] ]
		else :
			linecoords = [ s0[0], s0[1], s[0], s[1], t[0], t[1], tA[0], tA[1] ]

		self.connection2line[(sb, t0, tb, t1)] = (line, linecoords)
		self.canv.coords(line, *linecoords)
		self.model.set_connection_meta(sb, t0, tb, t1, { "path" : linecoords })

	# ----------------------------------------------------------------------------------------------------

	#TODO line_edit_data = namedtuple("line_edit_data", ["x"])
	
	def get_nearest(self, x, y, ssz = 4) :
		o = self.canv.find_overlapping(x-ssz, y-ssz, x+ssz, y+ssz)
		filtered_old = ((o, list(filter(lambda v: o[0] == v[1][0], self.connection2line.items())))
			if o else (None, None))
		filtered = ((o, [ v for v in self.connection2line.items() if o[0] == v[1][0] ])
			if o else (None, None))
		assert(filtered==filtered_old)
#		print "get_nearest:", o, filtered
		return filtered

	def default_mousedown(self, ee) :

		self.canv.focus_set()

		e = event_t(self.canv.canvasx(ee.x), self.canv.canvasy(ee.y), ee.state)

		self.canv.focus_set()
		self.clear_selection()
		if self.manipulating or e.state & BIT_SHIFT:
			return None
		self.move_start = e
		self.manipulating = False
		_, item = self.get_nearest(e.x, e.y)
		if item :
			route = item[0][1][1] # XXX XXX XXX fuckoff!!!
			kneebonus = 4
			indices = range(0, len(route)-2, 2)

			dist = ([ ((i, 2), mathutils.pldist(*(route[i:i+4]+[e.x, e.y]))) for i in indices ] +
				[ ((i, 1), mathutils.ppdist(*(route[i:i+2]+[e.x, e.y]))-kneebonus) for i in indices ])
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
#			print here(), self.mdata
#			self.model.begin_edit()

		else :
			self.selection_rect = self.create_selection_rect(e.x, e.y, e.x, e.y)
#			self.create_selection([])

#		(sb, t0, tb, t1), (canv_line, linecoords) = self.mdata
#		meta = self.model.get_connection_meta(sb, t0, tb, t1)
#		print here(), "old:", meta["path"]


	def default_mousemove(self, ee) :
		e = event_t(self.canv.canvasx(ee.x), self.canv.canvasy(ee.y), ee.state)

#		(sb, t0, tb, t1), (canv_line, _) = self.mdata
#		meta = self.model.get_connection_meta(sb, t0, tb, t1)
#		print here(), "old:", meta["path"]

		if self.manipulating == "connection" :
			diffX, diffY = (e.x - self.move_start.x), (e.y - self.move_start.y)
			self.move_start = e
			indices = range(self.mdata2[0], self.mdata2[0]+(self.mdata2[1]*2), 2)
			wire, (canv_line, old_path) = self.mdata
			path = list(old_path)
#			path = list(self.mdata[1][1])
			for i in indices :
				if i > 0 and (i + 2) < len(path) :
					path[i] += diffX
					path[i + 1] += diffY
			#self.connection2line[(sb, st, tb, tt)] = (line, linecoords)
			self.canv.coords(self.mdata[1][0], *path)
			self.mdata = wire, (canv_line, path)
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

		if self.manipulating == "connection" :
			(sb, t0, tb, t1), (canv_line, linecoords) = self.mdata
#			print here(), (sb, t0, tb, t1), linecoords
#			meta = self.model.get_connection_meta(sb, t0, tb, t1)
#			print here(), "old:", meta["path"]
#			print here(), "new:", linecoords
			self.model.begin_edit()
			self.model.set_connection_meta(sb, t0, tb, t1, { "path" : linecoords })
			self.model.end_edit()

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
		if blocks or lines :
			x, y, r, b, = self.measure_objects(blocks, lines)
			self.selection_rect = self.create_selection_rect(x, y, r, b)
			self.selection = selection_t(blocks, lines)
			self.resize_selection()

	def create_selection_from_area(self, x, y, r, b) :
		self.clear_selection()
		selected = self.canv.find_enclosed(x, y, r, b)
		if selected :
#			lns = filter(lambda v: v[1][0] in selected, self.connection2line.items())
			blcks = [ self.window_index[w] for w in selected if w in self.window_index ]
			lns = [ v for v in self.connection2line.items() if v[1][0] in selected ]
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
					[ self.canv.bbox(w) for _, (w, _) in selected_lines ])
		if selected_blocks :
			blocks = reduce(mathutils.max_rect,
				[ self.canv.bbox(b.window) for b in selected_blocks ])
		if blocks and lines :
			return mathutils.max_rect(blocks, lines) 
		else :
			return blocks if blocks else lines

	def resize_selection(self) :
		b = self.measure_selection()
#		if b == None :
#			self.clear_selection()
#			return None
		m = cfg.SELECTION_RECT_SIZE
		self.canv.coords(self.selection_rect, b[0]-m, b[1]-m, b[2]+m, b[3]+m)

	def create_selection_rect(self, x0, y0, x1, y1) :
#		print(x1, y1)
		a = 4
		c = 4
		b = 0
		w_lt = Canvas(self)
#		pad_lt = self.canv.create_window(w_lt, x0-a, y0-a, x0+c, y0+c, fill="black") # left-top
#		pad_lt = self.canv.create_rectangle(x0-a, y0-a, x0+a, y0+a, fill="black") # left-top
#		pad_lb = self.canv.create_rectangle(x0-a, y1-a, x0+a, y1+a, fill="black") # left-bottom
#		pad_rt = self.canv.create_rectangle(x1-a, y0-a, x1+a, y0+a, fill="black") # right-top
#		pad_rb = self.canv.create_rectangle(x1-a, y1-a, x1+a, y1+a, fill="black") # right-bottom
#		rct = self.canv.create_rectangle(x0, y0, x1, y1, dash=(2,2), fill=None)
		rct = self.canv.create_rectangle(x0-b, y0-b, x1+b, y1+b, dash=(2,2), fill=None)
		return rct

	def clear_selection(self) :
		if self.selection_rect :
			self.canv.delete(self.selection_rect)
			self.selection_rect = None
			self.selection = None

#TODO move to dfs
	@editing
	def delete_selection(self) :
		if self.selection :
			for connection, data in self.selection.lines :
				self.model.remove_connection(*connection)
			for block in self.selection.blocks :
				self.model.remove_block(block.model)
			self.clear_selection()
			self.__raise_changed_event()#XXX decorator?

	#TODO optimize (blockmodel.geo = (pos, size, angles) ...)
#TODO move to dfs
	#XXX create editor model/move to dfs?
	@editing	
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
			self.__raise_changed_event()#XXX decorator?

#TODO move to dfs
	@editing	
	def move_selection(self, x, y) :
		if self.selection :
			for b in self.selection.blocks :
				if x :
					b.model.left += x
				if y :
					b.model.top += y
			self.resize_selection()
			self.__raise_changed_event()#XXX decorator?

	def select_next(self) :
		if self.selection :
			print("TODO select_next")

	# ----------------------------------------------------------------------------------------------------

	def serialize_selection(self) :
		if self.selection :
			data = get_dfs_model_data2(
				[ b.model for b in self.selection.blocks ],
				{ (b0, t0) : [(b1, t1)] for (b0, t0, b1, t1), _ in self.selection.lines },
				{ k : self.model.connections_meta[k] for k, _ in self.selection.lines },
				{} )
			return pickle.dumps(data)

	@editing	
	def paste(self, serialized) :
		try :
			types, struct, meta = pickle.loads(serialized)
		except :
			return None
#		print "paste:", types, struct, meta
#		load_to_dfs_model(self.model, types, struct, meta)
		bm, lm = load_to_dfs_model(self.model, types, struct, meta,
			self.__workbench_getter().blockfactory, deserializing=True)
		self.create_selection_from_list([ self.block_index[b] for b in bm ],
			[ (l, self.connection2line[l]) for l in lm ] )
		self.__raise_changed_event()#XXX decorator?

	# ----------------------------------------------------------------------------------------------------

	@editing
	def paste_block_on_mouse_down(self, e) :
		if not self.__paste_proto :
			return None
		b = BlockModel(self.__paste_proto, self.model, left=e.x, top=e.y)
		self.model.add_block(b)
#		if not bool(e.state & BIT_SHIFT) :
#			self.end_paste_block()
		self.__raise_changed_event()#XXX decorator? @editing?

	def end_paste_block(self) :
		self.__paste_proto = None
		self.canv.config(cursor="arrow")
		self.canv.bind("<ButtonPress-1>", self.default_mousedown)

	def begin_paste_block(self, proto) :  # TODO weird, make it not weird
		if proto :
			self.canv.config(cursor="plus")
			self.__paste_proto = proto
			self.canv.bind("<ButtonPress-1>", self.paste_block_on_mouse_down)
		else :
			self.canv.config(cursor="arrow")

	# ----------------------------------------------------------------------------------------------------

	def get_model(self) :
		return self.model

	def set_model(self, model, deserializing=False) :
		self.reset_state()
		if model :
			self.set_model(None)
			self.model = model
			self.model.add_listener(self)
			self.model.enum(deserializing=deserializing)
		else :
			if self.model :
				self.model.remove_listener(self)
			self.model = None
			self.canv.delete(ALL)

#	def set_changed(self, v) :
#		print "not implemented: set_changed"

#	changed = property(lambda self: True if self.model else False, set_changed)

	def do_undo(self) :
		self.model.undo()
		self.__raise_changed_event()#XXX decorator?

	def do_redo(self) :
		self.model.redo()
		self.__raise_changed_event()#XXX decorator?

	def __raise_changed_event(self) :
		if self.changed_event :
			self.changed_event()

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
		self.canv.config(cursor="arrow")

	def cancel_action_pending(self) :
		if self.__paste_proto is None :#self.selection_rect :
			self.clear_selection()
		else :
			self.end_paste_block()

	def popup(self, e) :
		self.cancel_action_pending()
		self.canv.focus_set()
		self.ui.editor_popup.tk_popup(e.x_root, e.y_root, 0)

	def __init__(self, ui, parent, workbench_getter) :

		self.ui = ui

#		self.__changed = False # XXX destroy

#		self.font = tkFont.nametofont("TkDefaultFont")
		self.font = tkFont.Font(font=self.ui.font_settings)
#		self.font_v = tkFont.nametofont("TkDefaultFont")
		self.txt_height = self.font.metrics("linespace")

		Frame.__init__(self, parent)

		self.__paste_proto = None
		self.__workbench_getter = workbench_getter

		self.grid(column=0, row=0, sticky=(N, W, E, S))

		self.canvas_scrollregion = (0, 0, cfg.CANVAS_WIDTH, cfg.CANVAS_HEIGHT)
		self.canv = Canvas(self, scrollregion=self.canvas_scrollregion,
			bg="white", highlightthickness=0)
		self.canv.grid(column=0, row=0, sticky=(W, E, N, S))
		self.canv.columnconfigure(0, weight=1)
		self.canv.rowconfigure(0, weight=1)
		self.canv.focus_set()

		yscroll = Scrollbar(self, orient=VERTICAL, command=self.canv.yview)
		yscroll.grid(column=1, row=0, sticky=(N,S))
		self.canv.configure(yscrollcommand=yscroll.set)

		xscroll = Scrollbar(self, orient=HORIZONTAL, command=self.canv.xview)
		xscroll.grid(column=0, row=1, sticky=(W,E))
		self.canv.configure(xscrollcommand=xscroll.set)

		self.reset_state()

		self.changed_event = None

		#XXX some of them might be bound to menu items
		self.canv.bind("<ButtonPress-1>", self.default_mousedown)
		self.canv.bind("<B1-Motion>", self.default_mousemove)
		self.canv.bind("<ButtonRelease-1>", self.default_mouseup)
#		self.canv.bind("<Delete>", lambda a: self.delete_selection())
		self.canv.bind("<Escape>", lambda a: self.cancel_action_pending())
		self.canv.bind("<l>", lambda e: None if get_basic_mod_keys(e.state) else self.rotate_selection(0, 0, -90))
		self.canv.bind("<r>", lambda e: None if get_basic_mod_keys(e.state) else self.rotate_selection(0, 0, 90))
		self.canv.bind("<h>", lambda e: None if get_basic_mod_keys(e.state) else self.rotate_selection(0, 180, 0))
		self.canv.bind("<v>", lambda e: None if get_basic_mod_keys(e.state) else self.rotate_selection(180, 0, 0))
		self.canv.bind("<Left>", lambda a: self.move_selection(-cfg.GRID_SIZE, 0))
		self.canv.bind("<Right>", lambda a: self.move_selection(cfg.GRID_SIZE, 0))
		self.canv.bind("<Up>", lambda a: self.move_selection(0, -cfg.GRID_SIZE))
		self.canv.bind("<Down>", lambda a: self.move_selection(0, cfg.GRID_SIZE))
		self.canv.bind("<Tab>", lambda a: self.select_next())
		self.canv.bind("<ButtonPress-3>", self.popup)

#		self.canv.config(cursor="plus")
#		self.canv.config(cursor="arrow")

		#XXX cursor: select, shift+cursor: move ?
		
		#self.canv.bind("<Motion>", lambda e: pprint((e.x, e.y)))

# ------------------------------------------------------------------------------------------------------------

class BlockEditorWindow(object) :

	def show_warning(self, msg) :
		try :
			tkMessageBox.showwarning(cfg.APP_NAME, msg, parent=self.root)
		except :
			pass


	def mnu_edit_cut(self, a=None) :
		if self.bloced.selection :
			pyperclip.setcb(self.bloced.serialize_selection())
			self.bloced.delete_selection()


	def mnu_edit_copy(self, a=None) :
		if self.bloced.selection :
			pyperclip.setcb(self.bloced.serialize_selection())


	def mnu_edit_paste(self, a=None) :
		self.bloced.paste(pyperclip.getcb())#XXX lambda?


	def mnu_edit_delete(self, a=None) :
		self.bloced.delete_selection()#XXX lambda?


	def mnu_edit_undo(self, a=None) :
		self.bloced.do_undo()#XXX lambda?
#		if self.bloced.undo :
#			self.bloced.undo.undo()


	def mnu_edit_redo(self, a=None) :
		self.bloced.do_redo()#XXX lambda?
#		if self.bloced.undo :
#			self.bloced.undo.redo()


	def mnu_edit_select_all(self, a=None) :
		self.bloced.select_all()


	def mnu_edit_comment(self, a=None) :
		pass


	def mnu_edit_uncomment(self, a=None) :
		pass


	def begin_paste_block(self, prototype) :
		self.bloced.begin_paste_block(prototype)
		self.last_block_inserted = prototype


	def mnu_blocks_insert_last(self, a=None) :
		if self.last_block_inserted :
			self.begin_paste_block(self.last_block_inserted)


	def implement(self) :
		pass
#		out = implement_dfs(self.bloced.get_model(), None)
#		print("out:", out)


	def close_window(self, a=None) :
		if self.__changed :
			ans = tkMessageBox.askquestion(type=tkMessageBox.YESNOCANCEL, title=cfg.APP_NAME,
				message=cfg.SAVE_BEFORE_CLOSE, default=tkMessageBox.YES)
			if ans == tkMessageBox.CANCEL:
				return None
			elif ans == tkMessageBox.YES :
				if not self.save_current_file() :
					return None
		self.work.finish()
		self.__save_user_settings()
		self.root.destroy()


	def confirm_complete_clear(self) :
		if self.__changed :
			ans = tkMessageBox.askquestion(type=tkMessageBox.OKCANCEL, title=cfg.APP_NAME,
				message=cfg.UNSAVED_DATA_WILL_BE_LOST, default=tkMessageBox.OK)
			return ans == tkMessageBox.OK
		return True
#			if ans == tkMessageBox.CANCEL:
#				return None
#			elif ans == tkMessageBox.OK :
#				if not self.save_current_file() :
#					return None



	def __on_closing(self) :
		self.close_window()

	# ----------------------------------------------------------------------------------------------------

	def __convert_mnu_text(self, text) :
		under = text.find("&")
		return ( text[0:under]+text[under+1:] if under != -1 else text,
			 under if under != -1 else None )


	def __convert_accel(self, accel) :
		parts = accel.replace("Ctrl", "Control").split("+")
		parts[-1] = parts[-1].lower() if len(parts[-1]) == 1 else parts[-1]
		return "<" + "-".join(parts) + ">"


	def __add_menu_item(self, mnu, item, index=None) :
		menu = None
		if isinstance(item, SepMnu) :
			menu = mnu.add_separator()
		else :
			menu = self.__add_submenu_item(mnu, item, index=index)
#			self.__add_submenu_item(*((mnu, )+item+(tuple() if len(item)==5 else (None,))))
		return menu


	def __add_submenu_item(self, parent, item, index=None) :
		if item.text :
			txt, under = self.__convert_mnu_text(item.text)
		if item.accel :
			self.root.bind(self.__convert_accel(item.accel), item.handler)
		if index is None :
			parent_add = parent.add
		else :
			parent_add = partial(parent.insert, index)
		if isinstance(item, CascadeMnu) :
			mnu = Menu(parent)
			self.__menu_items[item] = (parent, index)
#			print here(), item, parent
			parent_add("cascade", label=item.text, menu=mnu)
			for itm, mnu_index in zip(item.items, count()) :
				self.__add_menu_item(mnu, itm)
				self.__menu_items[itm] = (mnu, mnu_index)
#				print here(), itm, mnu
		elif isinstance(item, RadioMnu) or isinstance(item, CheckMnu) :
			if parent in self.__menu_vars :
				var = self.__menu_vars[parent]
			else :
				self.__menu_vars[parent] = var = StringVar()
#			print here(), parent, item.text
			item_type = "radiobutton" if isinstance(item, RadioMnu) else "checkbutton" #XXX ugly!!!
			val = item.value if item.value else item.text
			parent_add(item_type, label=txt, underline=under,
				command=partial(item.handler, var) if item.handler else None,
				accelerator=item.accel, variable=var,
				value=val)
			if item.selected :
				var.set(val)
		elif isinstance(item, CmdMnu) :
			parent_add("command", label=txt, underline=under,
				command=item.handler, accelerator=item.accel)
#		else :
#			parent.add(item_type, label=txt, underline=under,
#				command=handler, accelerator=accel)
#		self.__menu_items[item] = menu


	def add_top_menu(self, text, items=[], root=None) :
		if root is None :
			root = self.__menubar
		mnu = Menu(root)
		txt, under = self.__convert_mnu_text(text)
		root.add_cascade(menu=mnu, label=txt, underline=under)
		for item, i in zip(items, count()) :
			self.__add_menu_item(mnu, item, index=i)
			self.__menu_items[text] = (mnu, i)
		return mnu


	def replace_cascade(self, old, new) :
#		print(here(), new.text, old.text)
		mnu, index = self.__menu_items.pop(old)
		if old in self.__menu_vars :
			print here(), self.__menu_vars.pop(old)
#		print(here(), mnu, index, new.text, old.text)
		mnu.delete(index)
		self.__add_submenu_item(mnu, new, index=index)

	# ----------------------------------------------------------------------------------------------------

	def __set_current_file_name(self, fname) :
		self.__fname = fname
		if fname :
			title = "%s (%s)" % (os.path.basename(fname), os.path.dirname(fname))
		else :
			title = cfg.NONE_FILE
		self.root.title(("*" if self.__changed else "") + title + " - " + cfg.APP_NAME)


#	file_changed = property(lambda self: self.bloced.changed, lambda self, v: self.bloced.set_changed(v))
	have_file = property(lambda self: self.__fname != None)
	current_filename = property(lambda self: self.__fname)


	def __changed_event(self) :
		self.__changed = True
		self.__set_current_file_name(self.__fname)


	def open_file(self, a=None) :
		fname = askopenfilename(filetypes=KNOWN_EXTENSIONS)
		if fname :
			self.open_this_file_new(fname)


	def save_file_as(self) :
		return self.save_file(asksaveasfilename(filetypes=KNOWN_EXTENSIONS))


	def save_current_file(self, a=None) :
		return self.save_file(self.current_filename if self.have_file else asksaveasfilename(filetypes=KNOWN_EXTENSIONS))


	def new_file(self, a=None) :
		if not self.confirm_complete_clear() :
			return None
		self.work.clear()
		self.work.add_sheet(name=self.work.get_free_sheet_name(seed=cfg.SHEET_NAME_SEED))
		self.__changed = False
		self.__set_current_file_name(None)


	def open_this_file_new(self, fname) :
		if not self.confirm_complete_clear() :
			return None
		self.work.clear()
		try :
			with open(fname, "rb") as f :
				unpickle_workbench(f, self.work) 
		except IOError :
			self.show_warning("Failed to open file '{0}'".format(fname))
		else :
			self.__set_current_file_name(fname)
			self.__changed = False
			self.__update_recent_files(fname)
			self.__select_board(self.work.get_board())
			self.__select_port(self.work.get_port())


	def save_file(self, fname) :
		if fname :
			try :
				with open(fname, "wb") as f :
					pickle_workbench(self.work, f)
			except IOError :
				self.show_warning("Failed to open file '{0}'".format(fname))
			else :
				self.__changed = False
				self.__set_current_file_name(fname)
				self.__update_recent_files(fname)
				return True
		return False


	def mnu_mode_build(self, a=None) :
		self.work.build()


	def mnu_mode_run(self, a=None) :
		if not self.work.have_blob() :
			self.work.build()
		self.work.upload()


	def __save_user_settings(self) :
		self.__settings.main_width = self.root.winfo_width()
		self.__settings.main_height = self.root.winfo_height()
#		self.__settings.main_left, self.__settings.main_top = self.root.winfo_rootx(), self.root.winfo_rooty()
		with open("usersettings.pickle", "wb") as f :
			pickle.dump(self.__settings, f)


	def mkmac(self) :
		pass
#		try_mkmac(self.bloced.model)


	def __choose_port(self, *a, **b) :
		print(here(), self.work.get_port(), " ->", a[0].get())
		self.work.set_port(a[0].get())


	def __choose_board(self, *a, **b) :
		print(here(), self.work.get_board(), " ->", a[0].get())
		self.work.set_board(a[0].get())


	def __tick(self) :
		self.work.fire_callbacks()
#		messages = self.work.read_messages()
#		if messages :
#			print(messages)
		self.root.after(cfg.POLL_WORKERS_PERIOD, self.__tick)


	def __workbench_status_changed(self, job, is_ok, reason) :
		print("workbench changed", job, is_ok, reason)
		if job == "build" :
			if reason == "build_started" :
				msg = "build started ..."
			else :
				msg = "build ok" if is_ok else "build failed"
			self.status_label_right.configure(text=msg)
#		self.status_label_left.configure(text=columns[-1])


	def get_bloced(self) :
		win = self.tabs.select()
		return self.__tab_children[win]


	bloced = property(get_bloced)


	def __select_sheet(self, name) :
		sheet, bloced = self.__sheets[name]
		bloced.changed_event = self.__changed_event
		self.tabs.select(bloced)
#		print here(), name, bloced, self.tabs.select(), str(bloced)


	def add_sheet(self, sheet, name) :
		bloced = BlockEditor(self, self.tabs, self.__workbench_getter)
		bloced.grid(column=0, row=1, sticky=(W, E, N, S))
		bloced.columnconfigure(0, weight=1)
		bloced.rowconfigure(0, weight=1)
#		print here(), name, sheet
		bloced.set_model(None)
		assert(not (sheet is None))
#		bloced.set_model(GraphModel() if sheet is None else sheet)
		bloced.set_model(sheet)
#		self.__changed = False
#		self.__set_current_file_name(None)
		self.tabs.add(bloced, text=name)
		self.__sheets[name] = (sheet, bloced)#XXX
		self.__tab_children[str(bloced)] = bloced
#		print here(), self.__tab_children
		self.__select_sheet(name)


	def __change_callback(self, w, event, data) :
		print(here(), w, event, data)
		sheet_name = None
		changed = False
		if event == "sheet_added" :
			sheet, sheet_name = data #?
			self.add_sheet(sheet, sheet_name)
			changed = True
		elif event == "sheet_deleted" :
			sheet, sheet_name = data #?
			self.delete_sheet(sheet, sheet_name)
			changed = True
#		if changed :
#			self.__changed_event()
		if not sheet_name is None :
			if core.is_macro_name(sheet_name) or core.is_function_name(sheet_name) :
				self.__list_local_block()


	def begin_paste_local_block(self, sheet_name) :
		sheet = self.work.sheets[sheet_name]
		try :
			proto = core.create_proto_from_sheet(sheet_name, sheet)
		except Exception as e :
			proto = None
		if proto is None :
			print(here(), e) #TODO say something to user
		else :
			self.begin_paste_block(proto)


	def __list_local_block(self) :
		sheets = core.get_block_sheets(self.work)
		cmds = [ CmdMnu(core.sheet_block_name(sheet_name), None, partial(self.begin_paste_local_block, sheet_name))
			for sheet_name in sheets ]
#		print here(), cmds
		old = self.local_blocks_mnu_edit
		self.local_blocks_mnu_edit = CascadeMnu("Workbench", cmds)
		self.replace_cascade(old, self.local_blocks_mnu_edit)
		old = self.local_blocks_mnu_cntxt
		self.local_blocks_mnu_cntxt = CascadeMnu("Workbench", cmds)
		self.replace_cascade(old, self.local_blocks_mnu_cntxt)


	def delete_sheet(self, sheet, name) :
		print(here(), sheet, name, self.__tab_children)
		sheet, bloced = self.__sheets.pop(name)
		self.__tab_children.pop(str(bloced))
		self.tabs.forget(str(bloced))
#		for name, (sheet, bloced) in self.__sheets :
#			if str(bloced)


	def __open_recent(self, fname) :
		self.open_this_file_new(fname)


	def __list_recent_files(self, files) :
		old = self.__recent_menu
		mnu_item = lambda f, i : CmdMnu("&{0}. {1}".format(i+1, os.path.basename(f)),
			None, partial(self.__open_recent, f))
		self.__recent_menu = CascadeMnu("Recent files",
			[ mnu_item(f, i) for f, i in zip(files, count()) ])
		if not old is None :
			self.replace_cascade(old, self.__recent_menu)
		return self.__recent_menu


	def __update_recent_files(self, fname) :
		f = os.path.abspath(fname)
		try :
			self.__settings.recent_files.remove(f)
		except ValueError :
			pass
		self.__settings.recent_files.insert(0, f)
		self.__list_recent_files(self.__settings.recent_files)


	def __import_sheet(self, filename) :
		title = os.path.splitext(os.path.basename(filename))[0]
		try :
			with open(filename, "rb") as f :
				m = unpickle_dfs_model(f, lib=self.work.blockfactory)
			self.work.add_sheet(sheet=m, name=title)
		except IOError :
			self.show_warning("Failed to import file '{0}'".format(filename))


	def __mnu_import_sheet(self, a=None) :
		print(here())
		fname = askopenfilename(filetypes=IMPORT_EXTENSIONS)
		if fname :
			self.__import_sheet(fname)


	def __mnu_add_sheet(self, a=None) :
		d = InputDialog(self.root, "Enter name for new sheet",
			initial=self.work.get_free_sheet_name())
#		print here(), d.value
		if d.value :
			self.work.add_sheet(sheet=None, name=d.value)


	def __mnu_export_sheet(self, a=None) :
#TODO
		pass


	def __mnu_delete_sheet(self, a=None) :
		win = self.tabs.select()
		print(win, self.tabs.index(win))
		subwin = self.__tab_children[win]
		for name, (sheet, bloced) in self.__sheets.items() :
			if bloced == subwin :
				self.work.delete_sheet(name=name)
				break


	def __open_example(self, a=None) :
		self.open_this_file_new(a)


	def __list_examples(self) :
		workdir = os.path.join(os.getcwd(), "examples")
		tree = os.walk(workdir)
		l = []
		#don't recurse
		for root, dirs, files in islice(tree, 1) : #tree if recurse else islice(tree, 1) :
			l += [ os.path.join(workdir, root, fn) for fn in files ]
		_, ext = WORKBENCH_EXTENSION
		result = fnmatch.filter(l, ext)
		return result


	def __select_board(self, board) :
#		xxx = self.__menu_items[self.__board_menu.items[0]]
		var = self.__menu_vars[self.__menu_items[self.__board_menu.items[0]][0]]
#		print here(), type(var)#xxx, xxx[0] in self.__menu_vars
		var.set(board)


	def __select_port(self, port) :
		if not self.__port_menu :
			return None
		mnu_item = self.__menu_items[self.__port_menu.items[0]][0]
		if mnu_item in self.__menu_vars :
			var = self.__menu_vars[mnu_item]
			var.set(port)


	def __workbench_getter(self) :
		return self.work


	def __port_list_changed(self) :
#		print "ports changed", self.work.get_port_list()
		choice = self.work.get_port()
		old = self.__port_menu
		self.__port_menu = CascadeMnu("Serial Port",
			[ CmdMnu("&Rescan", None, self.__mnu_rescan_ports), SepMnu() ] +
			[ RadioMnu(p, None, self.__choose_port, selected=p==choice)
				for p, desc, nfo in self.work.get_port_list()])
		self.replace_cascade(old, self.__port_menu)
		self.__select_port(self.work.get_port())


	def rescan_ports(self) :
		self.work.rescan_ports()
		self.__port_list_changed()


	def __mnu_rescan_ports(self, a=None) :
		self.rescan_ports()


	def __mnu_rename_sheet(self) :
		win = self.tabs.select()
		if not win in self.__tab_children :
			return None
		subwin = self.__tab_children[win]
		sheet_name = None
		for name, (sheet, bloced) in self.__sheets.items() :
			if bloced == subwin :
				sheet_name = name
				break
		if sheet_name is None :
			return None
		d = InputDialog(self.root, "Enter new sheet name",
			initial=sheet_name)
		new_name = d.value
		if d.value :
			self.work.rename_sheet(name=sheet_name, new_name=new_name)


	def lib_menu_items(self, local_blocks_mnu) :
		blocks = sorted(self.work.blockfactory.block_list, key=lambda b: 1 if b.library else 0)
		block_grouped = { k : tuple(blcklst) for k, blcklst in groupby(blocks, lambda b: 1 if b.library else 0) }
		builtin_blocks = block_grouped[0] if 0 in block_grouped else tuple()
		lib_blocks = block_grouped[1] if 1 in block_grouped else tuple()
		for cat, b_iter in groupby(builtin_blocks, lambda b: b.category) :
			yield CascadeMnu(cat,
				[ CmdMnu(proto.type_name, None, partial(self.begin_paste_block, proto)) for proto in b_iter ] )
		yield SepMnu()
		yield local_blocks_mnu
		if not lib_blocks :
			raise StopIteration()
		yield SepMnu()
		for cat, b_iter in groupby(lib_blocks, lambda b: b.category) :
			blocks_sorted = sorted(b_iter, key=lambda b: b.type_name)
			yield CascadeMnu(cat,
				[ CmdMnu(proto.type_name, None, partial(self.begin_paste_block, proto)) for proto in blocks_sorted ] )


	def __layout_reroute(self) :
		if self.bloced :
			self.bloced.layout_reroute()


	def __layout__equal_spacing(self, axis) :
		if self.bloced :
			self.bloced.equal_spacing(axis)


	def __layout_align(self, align) :
		if self.bloced :
			self.bloced.layout_align(align)


	def setup_menus(self) :

		self.last_block_inserted = None

#		self.bloced.changed_event = self.__changed_event

		self.__menubar = Menu(self.root)
		self.root["menu"] = self.__menubar

		self.__recent_menu = None
		self.__recent_menu = self.__list_recent_files(self.__settings.recent_files)

		examples = self.__list_examples()

		self.add_top_menu("&File", [
			CmdMnu("&New", "Ctrl+N", self.new_file),
			CmdMnu("&Open...", "Ctrl+O", self.open_file),
			CmdMnu("&Save", "Ctrl+S", self.save_current_file),
			CmdMnu("S&ave As...", "Shift+Ctrl+S", self.save_file_as),
			SepMnu(),
			CascadeMnu("Examples",
				[ CmdMnu(os.path.basename(f), None, partial(self.__open_example, f)) for f in examples ]),
			SepMnu(),
			self.__recent_menu,
#			SepMnu(),
#			CmdMnu("Export...", "Ctrl+E", self.__mnu_file_export),
			SepMnu(),
			CmdMnu("&Quit", "Alt+F4", self.close_window) ])

		mnu_undo = CmdMnu("&Undo", "Ctrl+Z", self.mnu_edit_undo)
		mnu_redo = CmdMnu("&Redo", "Shift+Ctrl+Z", self.mnu_edit_redo)
		mnu_cut = CmdMnu("Cu&t", "Ctrl+X", self.mnu_edit_cut)
		mnu_copy = CmdMnu("&Copy", "Ctrl+C", self.mnu_edit_copy)
		mnu_paste = CmdMnu("&Paste", "Ctrl+V", self.mnu_edit_paste)
		mnu_delete = CmdMnu("&Delete", "Delete", self.mnu_edit_delete)
		mnu_select_all = CmdMnu("Select &All", "Ctrl+A", self.mnu_edit_select_all)

		self.add_top_menu("&Edit", [
			mnu_undo,
			mnu_redo,
			SepMnu(),
			mnu_cut, #CmdMnu("Cu&t", "Ctrl+X", self.mnu_edit_cut),
			mnu_cut, #CmdMnu("&Copy", "Ctrl+C", self.mnu_edit_copy),
			mnu_paste, #CmdMnu("&Paste", "Ctrl+V", self.mnu_edit_paste),
			mnu_delete, #CmdMnu("&Delete", "Delete", self.mnu_edit_delete),
			SepMnu(),
			mnu_select_all, #CmdMnu("Select &All", "Ctrl+A", self.mnu_edit_select_all),
			SepMnu(),
			CmdMnu("Pr&eferences", None, self.mnu_edit_preferences)
			])


		self.local_blocks_mnu_edit = CascadeMnu("Workbench", [])
		block_list_edit = tuple(self.lib_menu_items(self.local_blocks_mnu_edit))
		self.add_top_menu("&Library",
#			[ CmdMnu("&Insert last", "Ctrl+B", self.mnu_blocks_insert_last), SepMnu() ] +
			block_list_edit)

		self.local_blocks_mnu_cntxt = CascadeMnu("Workbench", [])
		block_list_cntxt = tuple(self.lib_menu_items(self.local_blocks_mnu_cntxt))
		editor_menu = [ CascadeMnu("Library", block_list_cntxt),
			SepMnu(), mnu_undo, mnu_redo,
			SepMnu(), mnu_cut, mnu_copy, mnu_paste, mnu_delete,
			SepMnu(), mnu_select_all ]
		self.editor_popup = self.add_top_menu("", items=editor_menu, root=Menu(self.root))


		boards = [ (k, v["name"]) for k, v in self.work.get_board_types().items() ]

#		self.__port_menu = CascadeMnu("Serial Port",
#			[ RadioMnu(p, None, self.__choose_port) for p, desc, nfo in build.get_ports() ])
		self.__port_menu = CascadeMnu("(scanning)", [])

		self.__board_menu = CascadeMnu("Board",
			[ RadioMnu(txt, None, self.__choose_board, value=val) for val, txt in boards ])

		self.__model_menu = self.add_top_menu("&Workbench", [
			CmdMnu("&Build", "F6", self.mnu_mode_build),
			CmdMnu("&Run", "F5", self.mnu_mode_run),
#			CmdMnu("&Stop", "Ctrl+F5", None)
			SepMnu(),
			CmdMnu("Add sheet", "Shift+Ctrl+N", self.__mnu_add_sheet),
			CmdMnu("Rename sheet", None, self.__mnu_rename_sheet),
			CmdMnu("Import sheet", None, self.__mnu_import_sheet),
			CmdMnu("Export sheet", None, self.__mnu_export_sheet),
			CmdMnu("Delete sheet", None, self.__mnu_delete_sheet),
			SepMnu(),
			self.__board_menu,
			self.__port_menu,
			])

		self.__layout_menu = self.add_top_menu("L&ayout", [
			CmdMnu("Reroute", None, self.__layout_reroute),
			SepMnu(),
			CmdMnu("Make equal vertical spacing", None, partial(self.__layout__equal_spacing, "y")),
			CmdMnu("Make equal horizontal spacing", None, partial(self.__layout__equal_spacing, "x")),
			SepMnu(),
			CmdMnu("Align lefts", None, partial(self.__layout_align, "lefts")),
			CmdMnu("Align rights", None, partial(self.__layout_align, "rights")),
			CmdMnu("Align centers", None, partial(self.__layout_align, "centers")),
			CmdMnu("Align tops", None, partial(self.__layout_align, "tops")),
			CmdMnu("Align middles", None, partial(self.__layout_align, "middles")),
			CmdMnu("Align bottoms", None, partial(self.__layout_align, "bottoms")),
			])

		self.add_top_menu("&Help", [
			CmdMnu("&Content...", "F1", lambda *a: webbrowser.open(cfg.HELP_URL)),
			SepMnu(),
			CmdMnu("&About...", None, lambda *a: tkMessageBox.showinfo(cfg.APP_NAME, cfg.APP_INFO)) ])

		if 1 :
			self.add_top_menu("_Debu&g", [
				CmdMnu("delete menu", None, lambda *a: self.__model_menu.delete(3)),
				CmdMnu("Implement", None, self.implement),
				CmdMnu("test_text_editor", None, self.test_text_editor),
				CmdMnu("mkmac", None, self.mkmac),
				CmdMnu("geo", None, lambda *a: self.root.geometry("800x600+2+0")),
				CmdMnu("connections", None, lambda *a: pprint(self.bloced.get_model().get_connections())),
				CmdMnu("edit custom target", None, self.edit_custom_target), ])
#			menu_debug.add_command(label="zoom",
#				command=lambda: self.bloced.canv.scale(ALL, 0, 0, 2, 2))

		self.rescan_ports()


	def test_text_editor(self) :
		d = TextEditorDialog(self.root, "hello")
		if d.value :
			print(d.value)


	def edit_custom_target(self) :
		items = (
			("name", "(custom target name)"),
			("upload.protocol", "arduino"),
			("upload.maximum", "30720"),#mind size of bootloader
			("upload.speed", "57600"),#??
			("bootloader.low_fuses", "0xFF"),#??
			("bootloader.high_fuses", "0xDA"),#??
			("bootloader.extended_fuses", "0x05"),#??
			("bootloader.path", "atmega"),
			("bootloader.file", "a.hex"),
			("bootloader.unlock_bits", "0x3F"),#??
			("bootloader.lock_bits", "0x0F"),#??
			("build.mcu", "atmega328"),
			("build.f_cpu", "16000000L"),
			("build.core", "arduino"),
		)
		d = InputDialog(self.root, "Edit custom target",
			items=items)
		if d.value :
			pprint(d.value)


	def mnu_edit_preferences(self, a=None) :
		items = (
			("Arduino directory", ""),
		)
		d = InputDialog(self.root, "Edit Preferences",
			items=items)
		if d.value :
			pprint(d.value)


	def __load_default_config(self, config) :
		config.add_section("Path")
		config.set("Path", "all_in_one_arduino_dir", "")


#	@catch_all
	def __init__(self, load_file=None) :

		try :
			with open("usersettings.pickle", "rb") as f :
				self.__settings = pickle.load(f)
		except :
			self.__settings = UserSettings()
			print("failed to load user setting, defaults loaded")

		self.config = SafeConfigParser()
		config_file = os.path.join(os.getcwd(), "config.cfg")
		try :
			self.config.read(config_file)
			self.config.get("Path", "all_in_one_arduino_dir", None)
		except :
			self.__load_default_config(self.config)
			try :
				with open(config_file, "w") as cf :
					print here()
					self.config.write(cf)
			except :
				print(here(), "error while writing '" + config_file + "'")

		print here(), self.config.get("Path", "all_in_one_arduino_dir", None)

		self.__sheets = {}#XXX see __change_callback

		self.__tab_children = {}

		self.__fname = None
		self.__changed = False

		self.work = Workbench(
			lib_dir=os.path.join(os.getcwd(), "library"),
			config=self.config,
			passive=False,
			status_callback=self.__workbench_status_changed,
			ports_callback=self.__port_list_changed,
			change_callback=self.__change_callback)
		self.work.rescan_ports()

		self.__menu_items = {}
		self.__menu_vars = {}

		font_settings_t = namedtuple("font_settings", ("family", "size"))
		self.font_settings = font_settings_t("sans", 8)

		self.root = Tk()

		if 0 :
			self.root.option_add("*Font", self.font_settings)
			s = ttk.Style()
			s.configure('.', font=self.font_settings)

#		print tkFont.families()
		self.root.protocol("WM_DELETE_WINDOW", self.__on_closing)
#		print (tkFont.Font().actual())
#		print tkFont.families()

		self.root.title(cfg.APP_NAME)
		self.root.option_add("*tearOff", FALSE)
		self.root.columnconfigure(0, weight=1)
		self.root.rowconfigure(0, weight=1)

#		mainframe = Frame(self.root)
#		mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
#		mainframe.columnconfigure(0, weight=1)
#		mainframe.rowconfigure(1, weight=1)

		self.tabs = ttk.Notebook(self.root)
		self.tabs.grid(column=0, row=0, sticky=(N, W, E, S))
		self.tabs.columnconfigure(0, weight=1)
		self.tabs.rowconfigure(1, weight=1)
		self.tabs.enable_traversal()
#		f1 = ttk.Frame(self.tabs)

		self.statusbar = Frame(self.root, height=32)
		self.statusbar.grid(column=0, row=1, sticky=(N, W, E, S))
		self.statusbar.columnconfigure(0, weight=1)
		self.statusbar.columnconfigure(1, weight=1)

		self.status_label_left = Label(self.statusbar, text="left", relief=SUNKEN)
		self.status_label_left.grid(column=0, row=0, sticky=(N, W, S))

		self.status_label_right = Label(self.statusbar, text="right", relief=SUNKEN)
		self.status_label_right.grid(column=1, row=0, sticky=(N, E, S))

#		self.cons = Text(mainframe,height=10,background='white')
#		self.cons.grid(column=0, row=3, sticky=(W, E, S))
#		self.cons.rowconfigure(2, weight=0)

		self.setup_menus()

		self.root.geometry("%ix%i" % (self.__settings.main_width, self.__settings.main_height))
#		self.root.geometry("+%i+%i" % (self.__settings.main_left, self.__settings.main_top))
#		self.root.geometry("%ix%i+%i+%i" % (self.__settings.main_width, self.__settings.main_height,
#			self.__settings.main_left, self.__settings.main_top))
#TODO
#		thestate = window.state()
#		window.state('normal')
#		window.iconify()
#		window.deiconify()

		self.root.after(cfg.POLL_WORKERS_PERIOD, self.__tick)

		if load_file :
			self.open_this_file_new(load_file)
		else :
			self.new_file()#TODO possibly set draft file name, time+date+username or so

	def run(self) :
		self.root.mainloop()

# ------------------------------------------------------------------------------------------------------------

if __name__ == "__main__" :
#	be = BlockEditorWindow()
#	if len(sys.argv) == 2 :
#		be.open_this_file_new(os.path.abspath(os.path.join(os.path.curdir, sys.argv[1])))
#	be.root.mainloop()
	f = None
	if len(sys.argv) == 2 :
		f = os.path.abspath(os.path.join(os.path.curdir, sys.argv[1]))
	w = BlockEditorWindow(load_file=f)
	try :
		w.run()
	except :
		print("top level except")
		w.work.finish()
#		w.work._Workbench__set_should_finish()
#TODO kill threads!!!
		raise

# ------------------------------------------------------------------------------------------------------------

