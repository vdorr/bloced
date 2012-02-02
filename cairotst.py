
import cairo
import math
import Tkinter

#def _alpha_blending(rgba, back):
#	"Return a rgb tuple composed from a rgba and back(ground) tuple/list."
#	paired = zip(rgba[:-1], back)
#	alpha = rgba[-1]
#	tmp = list()
#	for upper, lower in paired:
#		blend = (((255 - alpha) * lower) + (alpha * upper)) / 255
#		tmp.append(blend)
#	return(tuple(tmp))

def convert(data, width, height):
	col = []
	rows = []
#	for i in range(0, len(data), 4) :
	for y in range(height) :
		rows.append("{")
		for i in range(y * 4 * height, (y+1) * 4 * height, 4) :
			rows.append("#{0:02x}{1:02x}{2:02x}".format(
				ord(data[i+2]),
				ord(data[i+1]),
				ord(data[i+0])))
#			if len(col) == width :
##				print(((i*4) % width))
#				rows.append("".join(("{ ", " ".join(col), " } ")))
#				col = []
		rows.append("}")
	print " ".join(rows)
	return " ".join(rows)


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

#	mat = ctx.get_font_matrix()
#	mat.rotate(math.pi*0.5)
#	ctx.set_font_matrix(mat)

	text = "Xx"
	x_bearing, y_bearing, w, h, x_advance, y_advance = ctx.text_extents(text)
#	print(w, h)
	ctx.move_to (20,20)
	ctx.show_text(text)

	root = Tkinter.Tk()

	image1 = Tkinter.PhotoImage(width=width, height=height)
	data = convert(surface.get_data(), width, height)
	image1.put(data)

	panel1 = Tkinter.Label(root, image=image1)
	panel1.pack(side='top', fill='both', expand='yes')
	panel1.image = image1
	root.mainloop()


if __name__ == "__main__" :
	main()



