#! /usr/bin/python2.7

import pygtk
#pygtk.require('2.0')
import gtk
import gtk.glade

from pprint import pprint
from functools import partial

from collections import namedtuple

# ------------------------------------------------------------------------------------------------------------

def is_gtk_handler(f) :
	return hasattr(f, "is_gtk_handler") and f.is_gtk_handler

def handler(f):
	f.is_gtk_handler = True
	return f

# ------------------------------------------------------------------------------------------------------------

qtnode_t = namedtuple("qtnode", ("x", "y", "w", "h", "q0", "q1", "q2", "q3", "items"))

def qt_make_root() :
	pass

def qt_add_item(root, item) :
	pass

def qt_remove_item(root, item) :
	pass

def qt_update_item(root, item) :
	pass

def rect_overlaps(x0, y0, w0, h0, x1, y1, w1, h1)
	return False

def qt_overlaps(root, x, y, w, h) :
	pass

# ------------------------------------------------------------------------------------------------------------

class GUI() :

	@handler
	def on_window1_destroy(self, obj) :
		gtk.main_quit()

	@handler
	def on_drawingarea1_expose_event(self, area, event) :

		self.style = self.drawingarea.get_style()
		self.gc = self.style.fg_gc[gtk.STATE_NORMAL]

		x, y = 310, 10
		points = [(x+10,y+10), (x+10,y), (x+40,y+30), (x+30,y+10), (x+50,y+10)]
		self.drawingarea.window.draw_lines(self.gc, points)

#		self.drawingarea.window.draw_rectangle(self.gc, False, x, y, 80, 70)
		self.drawingarea.window.draw_rectangle(self.gc, False, x+10, y+10, 20, 20)
		self.drawingarea.window.draw_rectangle(self.gc, False, x+50, y+10, 20, 20)
		self.drawingarea.window.draw_rectangle(self.gc, False, x+20, y+50, 40, 10)

#		print self.gc

	def __init__(self) :
		self.glade = gtk.glade.XML("bloced.glade")
#		self.window = self.glade.get_widget("window1")
		self.drawingarea = self.glade.get_widget("drawingarea1")

		self.glade.signal_autoconnect({ name : partial(f, self)
			for name, f in self.__class__.__dict__.items() if is_gtk_handler(f) })

# ------------------------------------------------------------------------------------------------------------

if __name__ == "__main__" :
	gui = GUI()
	gtk.main()

# ------------------------------------------------------------------------------------------------------------

