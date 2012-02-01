
import cairo
import math
import Tkinter
#import tkinter as Tkinter
import Image
import ImageTk
from os import linesep

class CairoImage(Tkinter.Image) :
	def __init__(self) :
		super(Tkinter.Image.__class__, self).__init__(self)
		pass

def make_xbm(w, h, data) :
	octets = []
	byte = 0
	bit = 0
	octet = 0
	state = False
	dots = 0
	for i in range(len(data)/4) :
		state = 0 if all([ 255==ord(data[i*4+j]) for j in range(4) ]) else 1
#		print state
		octet |= state << (bit)
		if bit == 7 :
			octets.append(hex(octet))
			octet = 0
			bit = 0
		else :
			bit += 1


#	for x in data :
#		p = ord(x[0])
#		if p == 0 :
##			print p, "!!!!!!!"
#			dots =+ 1
##		if byte % 2 == 0 :
##			state |= p != 0
#		if byte % 4 == 0 :

#			state |= p == 0

#			octet |= (1 if state else 0) << bit
#			if bit == 7 :
#				octets.append(hex(octet))
#				octet = 0
#				bit = 0
#			bit += 1
#			state = False
#		byte += 1

#	print(len(data), len(octets), byte, "dots=", dots)#, len(data) / len(octets))

	s = ("#define test_width %i" % w + linesep +
	"#define test_height %i" % h + linesep +
	"static char test_bits[] = {" + linesep +
	",".join(octets) + linesep +
	"};")

	return s

if __name__ == "__main__" :

	width, height = 64, 64

	surface = cairo.ImageSurface(cairo.FORMAT_RGB24, width, height)
	ctx = cairo.Context(surface)

	ctx.set_source_rgb (1, 1, 1)
	ctx.set_operator (cairo.OPERATOR_SOURCE)
	ctx.rectangle(0, 0, width, height)
	ctx.fill()

	ctx.set_source_rgb (0, 0, 0)
	ctx.select_font_face("Sans")
	ctx.set_font_size(11)
#	print(ctx.get_font_matrix())
	mat = ctx.get_font_matrix()
	mat.rotate(math.pi*0.5)
	ctx.set_font_matrix(mat)
#	print(mat)

	text = "Xx"
	x_bearing, y_bearing, w, h, x_advance, y_advance = ctx.text_extents(text)
#	print(w, h)
	ctx.move_to (20,20)
	ctx.show_text(text)

	surface.write_to_png('test.png')

	print make_xbm(width, height, surface.get_data())

#	ci = CairoImage()

	root = Tkinter.Tk()
	image1 = ImageTk.PhotoImage(Image.open("test.png"))
	panel1 = Tkinter.Label(root, image=image1)
	panel1.pack(side='top', fill='both', expand='yes')
	panel1.image = image1
	root.mainloop()





