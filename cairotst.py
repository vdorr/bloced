
import cairo
import math
import Tkinter
#import tkinter as Tkinter
import Image
import ImageTk
from os import linesep

def make_xbm(w, h, data) :
	octets = []
	byte = 0
	bit = 0
	octet = 0
	state = False
	dots = 0
	for i in range(len(data)/4) :
		pixel = [ ord(data[i*4+j]) for j in range(4) ]
		state = 0 if all([ 255==p for p in pixel ]) else 1
		if state :
			print pixel
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


def make_pgm(w, h, data) :
	s = ("P2"+ linesep +
	"{0} {0}".format(w, h) + linesep +
	"255" + linesep)

	octets = []
	byte = 0
	bit = 0
	octet = 0
	state = False
	dots = 0

	rows = []
	l = []
	col=0

	for i in range(len(data)/4) :
		pixel = [ ord(data[i*4+j]) for j in range(4) ]
		l.append(str(pixel[2]))
#		print str(pixel[2])
		col += 1
		if col == w :
			col = 0
			rows.append(" ".join(l))
			l = []

	return s + linesep.join(rows)

def _alpha_blending(rgba, back):
	"Return a rgb tuple composed from a rgba and back(ground) tuple/list."
	paired = zip(rgba[:-1], back)
	alpha = rgba[-1]
	tmp = list()
	for upper, lower in paired:
		blend = (((255 - alpha) * lower) + (alpha * upper)) / 255
		tmp.append(blend)
	return(tuple(tmp))

def convert(bgra_buffer, width, height):
	"Convert bgra buffer to photoimage put"
	idx = 0
	end = len(bgra_buffer)
	arguments = list()

	while idx < end:
#		rgba = (ord(bgra_buffer[idx + 2]),
#		ord(bgra_buffer[idx + 1]),
#		ord(bgra_buffer[idx + 0]),
#		ord(bgra_buffer[idx + 3]))
#		back = (255, 255, 255)
#		rgb = _alpha_blending(rgba, back)
		rgb = (ord(bgra_buffer[idx + 2]),
			ord(bgra_buffer[idx + 1]),
			ord(bgra_buffer[idx + 0]))
		arguments += rgb
		idx += 4

	template = ' '.join(height *['{%s}' % (' '.join(width*["#%02x%02x%02x"]))])

	return(template % tuple(arguments))


def main() :
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

#	surface.write_to_png('test.png')

#	data = make_pgm(width, height, surface.get_data())
#	print data
#	ci = CairoImage()

#	return None

	root = Tkinter.Tk()

#	img = Image.open("test.png")
#	image1 = ImageTk.PhotoImage(img)

#	image1 = RawImage(surface.get_data(), width, height)
#	image1 = Tkinter.PhotoImage(data=data)
#	image1 = Tkinter.PhotoImage(file = "balloons.pgm")

	image1 = Tkinter.PhotoImage(width=width, height=height)
	data = convert(surface.get_data(), width, height)
	image1.put(data)

	panel1 = Tkinter.Label(root, image=image1)
	panel1.pack(side='top', fill='both', expand='yes')
	panel1.image = image1
	root.mainloop()


if __name__ == "__main__" :
	main()



