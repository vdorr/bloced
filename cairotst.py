
import cairo
import math
import Tkinter
#import tkinter as Tkinter
import Image
import ImageTk
from os import linesep

#class CairoImage(Tkinter.Image) :
#	def __init__(self) :
#		super(Tkinter.Image.__class__, self).__init__(self)
#		pass

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

class RawImage(Tkinter.Image):
    """Widget which can display colored images in GIF, PPM/PGM format."""
    def __init__(self, data, width, height, name=None, cnf={}, master=None, **kw):
        """Create an image with NAME.

        Valid resource names: data, format, file, gamma, height, palette,
        width."""
#	self.__data = data
#	self.__width = width
#	self.__height = height
#	self.name = None
        Tkinter.Image.__init__(self, 'photo', name, cnf, master, **kw)
	pass

#    def blank(self):
#        """Display a transparent image."""
#        self.tk.call(self.name, 'blank')
#    def cget(self, option):
#        """Return the value of OPTION."""
#	print option
#        return self.tk.call(self.name, 'cget', '-' + option)
    # XXX config
#    def __getitem__(self, key):
#        return self.tk.call(self.name, 'cget', '-' + key)
    # XXX copy -from, -to, ...?
#    def copy(self):
#        """Return a new PhotoImage with the same image as this widget."""
#        destImage = PhotoImage()
#        self.tk.call(destImage, 'copy', self.name)
#        return destImage
#    def zoom(self,x,y=''):
#        """Return a new PhotoImage with the same image as this widget
#        but zoom it with X and Y."""
#        destImage = PhotoImage()
#        if y=='': y=x
#        self.tk.call(destImage, 'copy', self.name, '-zoom',x,y)
#        return destImage
#    def subsample(self,x,y=''):
#        """Return a new PhotoImage based on the same image as this widget
#        but use only every Xth or Yth pixel."""
#        destImage = PhotoImage()
#        if y=='': y=x
#        self.tk.call(destImage, 'copy', self.name, '-subsample',x,y)
#        return destImage



#    def get(self, x, y):
#        """Return the color (red, green, blue) of the pixel at X,Y."""
##        return self.tk.call(self.name, 'get', x, y)
#	i = (y * self.__width * 3) + (x * 3)
#	return self.__data[i+1], self.__data[i+2], self.__data[i+3]




#    def put(self, data, to=None):
#        """Put row formatted colors to image starting from
#        position TO, e.g. image.put("{red green} {blue yellow}", to=(4,6))"""
#        args = (self.name, 'put', data)
#        if to:
#            if to[0] == '-to':
#                to = to[1:]
#            args = args + ('-to',) + tuple(to)
#        self.tk.call(args)
#    # XXX read
#    def write(self, filename, format=None, from_coords=None):
#        """Write image to file FILENAME in FORMAT starting from
#        position FROM_COORDS."""
#        args = (self.name, 'write', filename)
#        if format:
#            args = args + ('-format', format)
#        if from_coords:
#            args = args + ('-from',) + tuple(from_coords)
#        self.tk.call(args)

class BmpImage:

    ##
    # Create a Tkinter-compatible bitmap image.
    # <p>
    # The given image must have mode "1".  Pixels having value 0 are
    # treated as transparent.  Options, if any, are passed on to
    # Tkinter.  The most commonly used option is <b>foreground</b>,
    # which is used to specify the colour for the non-transparent
    # parts.  See the Tkinter documentation for information on how to
    # specify colours.
    #
    # @def __init__(image=None, **options)
    # @param image A PIL image.

    def __init__(self, data, width, height):

#        # Tk compatibility: file or data
#        if image is None:
#            if kw.has_key("file"):
#                image = Image.open(kw["file"])
#                del kw["file"]
#            elif kw.has_key("data"):
#                from StringIO import StringIO
#                image = Image.open(StringIO(kw["data"]))
#                del kw["data"]

        self.__mode = "RGB"#image.mode
        self.__size = (width, height)

#        if _pilbitmap_check():
#            # fast way (requires the pilbitmap booster patch)
#            image.load()
#            kw["data"] = "PIL:%d" % image.im.id
        self.__im = data
#        else:
#            # slow but safe way
        kw={}
	kw["width"], kw["height"] = self.__size
        kw["data"] = data#image.tobitmap()
        self.__photo = apply(Tkinter.PhotoImage, (), kw)
        self.tk = self.__photo.tk
        self.paste(data)


    def __del__(self):
	pass
#        name = self.__photo.name
#        self.__photo.name = None
#        try:
#            self.__photo.tk.call("image", "delete", name)
#        except:
#            pass # ignore internal errors

    ##
    # Get the width of the image.
    #
    # @return The width, in pixels.

    def width(self):
        return self.__size[0]

    ##
    # Get the height of the image.
    #
    # @return The height, in pixels.

    def height(self):
        return self.__size[1]

    ##
    # Get the Tkinter bitmap image identifier.  This method is
    # automatically called by Tkinter whenever a BitmapImage object
    # is passed to a Tkinter method.
    #
    # @return A Tkinter bitmap image identifier (a string).

    def __str__(self):
        return str(self.__photo)

    def paste(self, im, box=None):
	pass
#        # convert to blittable
#        im.load()
#        image = im.im
#        if image.isblock() and im.mode == self.__mode:
#            block = image
#        else:
#            block = image.new_block(self.__mode, im.size)
#            image.convert2(block, image) # convert directly between buffers

#        tk = self.__photo.tk

#        try:
#            tk.call("PyImagingPhoto", self.__photo, block.id)
#        except Tkinter.TclError, v:
#            # activate Tkinter hook
#            try:
#                import _imagingtk
#                try:
#                    _imagingtk.tkinit(tk.interpaddr(), 1)
#                except AttributeError:
#                    _imagingtk.tkinit(id(tk), 0)
#                tk.call("PyImagingPhoto", self.__photo, block.id)
#            except (ImportError, AttributeError, Tkinter.TclError):
#                raise # configuration problem; cannot attach to Tkinter

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

#	print make_xbm(width, height, surface.get_data())

#	ci = CairoImage()

	root = Tkinter.Tk()

	img = Image.open("test.png")
#	print img
#	image1 = ImageTk.PhotoImage(img)
#	image1 = RawImage(surface.get_data(), width, height)
	image1 = BmpImage(surface.get_data(), width, height)

	panel1 = Tkinter.Label(root, image=image1)
	panel1.pack(side='top', fill='both', expand='yes')
	panel1.image = image1
	root.mainloop()





