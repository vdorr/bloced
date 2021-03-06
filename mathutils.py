
from math import sqrt
from collections import namedtuple
import sys

if sys.version_info.major == 3 :
	from functools import reduce

# ------------------------------------------------------------------------------------------------------------

#TODO docstring
#TODO tests

# ------------------------------------------------------------------------------------------------------------

rotate4_trig_tab = {
	0 :	(0, 1),
	90 :	(1, 0),
	180 :	(0, -1),
	270 :	(-1, 0),
	360 :	(0, 1),
}

def rotate4(orgx, orgy, x, y, angle) :
	sin_angle, cos_angle = rotate4_trig_tab[angle]
	nx = orgx + (((x - orgx) * cos_angle) + ((y - orgy) * sin_angle))
	ny = orgy + (((x - orgx) * sin_angle) + ((y - orgy) * cos_angle))
#	print "rotate4:", orgx, orgy, x, y, angle, (sin_angle, cos_angle), (nx, ny)
#	print "rotate4(2):",orgy, ((x - orgx) * sin_angle), ((y - orgy) * cos_angle)
	return nx, ny

def pldist(x1, y1, x2, y2, x, y) :
	#print "x1, y1, x2, y2, x, y", x1, y1, x2, y2, x, y #XXX
	n0, n1 = -y2+y1, x2-x1
	den = sqrt((n0**2)+(n1**2))
	return abs((x*n0)+(y*n1)+-(x1*n0)-(y1*n1))/den if den else ppdist(x1, y1, x, y)

def pldistex(x1, y1, x2, y2, x, y) :
	n0, n1 = -y2+y1, x2-x1
	den = sqrt((n0**2)+(n1**2))
	dist =  ((x*n0)+(y*n1)+-(x1*n0)-(y1*n1))/den if den else ppdist(x1, y1, x, y)
	return namedtuple("pl_t", ["dist", "intsc"])(
		abs(dist), (x-((dist*n0)/den), y-((dist*n1)/den)))

def ppdist(x1, y1, x2, y2) :
	return sqrt((x1-x2)**2+(y1-y2)**2)

def make_rect(x, y, w, h) :
	return [ (x, y), (x+w, y), (x+w, y+h), (x, y+h) ]

def __br_cmp(a, b) :
	(l0, t0, r0, b0), (l1, t1, r1, b1) = a, b
	return (l1 if l1 < l0 else l0,
		t1 if t1 < t0 else t0,
		r1 if r1 > r0 else r0,
		b1 if b1 > b0 else b0)

def bounding_rect(points) :
	(l, t, r, b) = reduce(__br_cmp,
		[ (x, y, x, y) for x, y in points ], 
		(1000000, 1000000, -1000000, -1000000))
	return l, t, r - l, b - t

#def bounding_rect(points) :
#	(l, t, r, b) = reduce(lambda (l0, t0, r0, b0), (l1, t1, r1, b1): (
#		l1 if l1 < l0 else l0,
#		t1 if t1 < t0 else t0,
#		r1 if r1 > r0 else r0,
#		b1 if b1 > b0 else b0),
#		[ (x, y, x, y) for x, y in points ],
#		(1000000, 1000000, -1000000, -1000000))
#	return l, t, r - l, b - t

def max_rect(a, b) :
	return ( b[0] if b[0] < a[0] else a[0],
		 b[1] if b[1] < a[1] else a[1],
		 b[2] if b[2] > a[2] else a[2],
		 b[3] if b[3] > a[3] else a[3] )

