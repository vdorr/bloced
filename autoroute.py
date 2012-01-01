
from collections import namedtuple
from itertools import product, zip_longest
from pprint import pprint

# ------------------------------------------------------------------------------------------------------------

#TODO docstring
#TODO tests?

# ------------------------------------------------------------------------------------------------------------

rct = namedtuple("rct", ["x", "y", "w", "h"])
vln = namedtuple("vln", ["x", "y1", "y2"])
hln = namedtuple("hln", ["y", "x1", "x2"])
pnt = namedtuple("pnt", ["x", "y"])

# ------------------------------------------------------------------------------------------------------------

def trln(p, b, r1, r2) :
	vals = [b[0], b[0] + b[2]]
	if p[1] >= r1[1] and p[1] <= (r1[1] + r1[3]) :
		vals += [r1[0], r1[0] + r1[2]]
	if p[1] >= r2[1] and p[1] <= (r2[1] + r2[3]) :
		vals += [r2[0], r2[0] + r2[2]]
	return (p[1],
		max(filter(lambda v : v <= p[0], vals)),
		min(filter(lambda v : v >= p[0], vals)),)

def transp(o) :
	if len(o) == 4 :
		return (o[1], o[0], o[3], o[2])
	else :
		return (o[1], o[0])

def intersect(l1, l2) :
	if type(l1) == type(l2) :
		#print l1,l2
		a1 = max([l1[1], l2[1]])
		a2 = min([l1[2], l2[2]])
		if l1[0] == l2[0] and a2 - a1 >= 0 :
			return (type(l1)(l1[0], a1, a2),
				(l1, l2))
	elif (l1 and l2 and
	      l1[0] >= l2[1] and l1[0] <= l2[2] and l2[0] >= l1[1] and l2[0] <= l1[2]) :
			return (pnt(l1[0] if type(l1) == vln else l2[0],
				    l2[0] if type(l1) == vln else l1[0]),
				    (l1, l2))
	else :
		return None

def trial_line(p, angle, b, r1, r2) :
	if angle in (0, 180) :
		y, x1, x2 = trln(p, b, r1, r2)
		return hln(y, x1, x2)
	elif angle in (90, 270) :
		x, y1, y2 = trln(transp(p), transp(b), transp(r1), transp(r2))
		return vln(x, y1, y2) 
	else :
		return None

# ------------------------------------------------------------------------------------------------------------

def my_lvl1_trlines(hl, vl, cut, g, b, r1, r2) :
	lns = izip_longest(
		map(lambda p : trial_line(pnt(p, hl.y), 90, b, r1, r2),
			xrange(cut.x - g + 1, hl[1], -g)),
		map(lambda p : trial_line(pnt(p, hl.y), 90, b, r1, r2),
			xrange(cut.x + g, hl[2], g)),
		map(lambda p : trial_line(pnt(vl.x, p), 0, b, r1, r2),
			xrange(vl[1], cut.y - g, g)),#XXX
			#xrange(cut.y - g - 1, vl[1], g)),
		map(lambda p : trial_line(pnt(vl.x, p), 0, b, r1, r2),
			xrange(cut.y + g, vl[2], g)),
		fillvalue = None)
	for tup in lns :
		for ln in filter(None, tup) :
			yield ln

# ------------------------------------------------------------------------------------------------------------

def mtroute_simple(s, t, b, r1, r2) :

	gridsz = 8

	trln_s = [ [ trial_line(s, 0, b, r1, r2),
		     trial_line(s, 90, b, r1, r2) ], [ ] ]

	trln_t = [ [ trial_line(t, 0, b, r1, r2),
		     trial_line(t, 90, b, r1, r2) ], [ ] ]
		     
	#print("trln_s", trln_s)	print("trln_t", trln_t)

	x = filter(None, map(lambda p: intersect(p[0], p[1]),
		product(trln_t[0], trln_s[0])))
	if x :
		is_simple = filter(lambda cr: type(cr[0]) != pnt, x)
		return [ s ] + ([] if is_simple else [ x[0][0] ]) + [ t ]

	tr_it_s = my_lvl1_trlines(trln_s[0][0], trln_s[0][1],
		s, gridsz, b, r1, r2)

	tr_it_t = my_lvl1_trlines(trln_t[0][0], trln_t[0][1],
		t, gridsz, b, r1, r2)

	next_trln = True
	trit, trit2, trln, trln2 = tr_it_s, tr_it_t, trln_s, trln_t

	while next_trln : #TODO use takewhile

		next_trln = next(trit, None)
		
		#if not next_trln : break
		
		trln[-1].append(next_trln)
		trit, trit2, trln, trln2 = trit2, trit, trln2, trln

		for lvl in trln : #TODO use dropwhile
			x = filter(None, map(lambda p: intersect(next_trln, p), lvl))
			if x :
				crossing, (next_trln, l2) = x[0]

				# solution is:
				# crossing of $next_trln and trial line of level 0 from $trln2
				# $crossing
				# if $l2 have level 1 - crossing of $l2 and trial line of level 0 from $trln

				q = filter(None, map(lambda p: intersect(next_trln, p), trln2[0]))
				solution = [ q[0][0], crossing ]
				if l2 in trln[1] :
					w = filter(None, map(lambda p: intersect(l2, p), trln[0]))
					solution.append(w[0][0])
				if trln == trln_s :
					solution.reverse()
				return [ s ] + solution + [ t ]

# ------------------------------------------------------------------------------------------------------------

def choose_bbox(r1, r2, win, margin) :
	x = min([ r1.x, r2.x ]) - margin
	y = min([ r1.y, r2.y ]) - margin
	w = max([ r1.x + r1.w, r2.x + r2.w ]) + margin - x
	h = max([ r1.y + r1.h, r2.y + r2.h ]) + margin - y
	return rct(
		x if x > win.x else win.x,
		y if y > win.y else win.y,
		w if w < win.w else win.w,
		h if h < win.h else win.h)

# ------------------------------------------------------------------------------------------------------------

