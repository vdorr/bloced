
from pprint import pprint
from collections import namedtuple
from implement import here


# ----------------------------------------------------------------------------


_rect_t = namedtuple("_rect_t", ("l", "t", "r", "b"))


class _node(object) :
	def __init__(self, parent_node, parent_quad, l, t, r, b) :
		self.parent_node = parent_node
		self.parent_quad = parent_quad
		self.extent = _rect_t(l, t, r, b)
		self.vertical = []
		self.horizontal = []
		self.quads = [ None, None, None, None ]


def qtree_init(w, h, get_obj_coords=lambda o: o) :
	return (_node(None, None, 0, 0, w, h), get_obj_coords)


__q_to_i = {
	(False, False) : 0,	#lb
	(False, True) : 1,	#lt
	(True, False) : 2,	#rb
	(True, True) : 3	#rt
}


def __q_extent(parent, qi) :
	pw = (parent.extent.r - parent.extent.l) / 2
	ph = (parent.extent.b - parent.extent.t) / 2
	l = parent.extent.l + ( 0 if qi in (0, 1) else pw)
	t = parent.extent.t + ( 0 if qi in (1, 3) else ph)
	return l, t, l+pw, t+ph

def qtree_insert(qt, o) :
	n, get_coords = qt
	cx = (n.extent.l + n.extent.r) / 2
	cy = (n.extent.t + n.extent.b) / 2
	o_l, o_t, o_r, o_b = get_coords(o)
#	print here(), cx, cy
	if o_l < cx < o_r :
		n.vertical.append(o)
	elif o_t < cy < o_b :
		n.horizontal.append(o)
	else :
		qi = __q_to_i[o_l < cx, o_t < cy]
		if n.quads[qi] == None :
			n.quads[qi] = _node(n, qi, *__q_extent(n, qi))
		qtree_insert((n.quads[qi], get_coords), o)


def __within(r, x=None, y=None) :
	return ( ( True if x is None else ( r.l < x < r.r ) ) and
	( True if y is None else ( r.t < y < r.b ) ) )

_V = 'V'
_H = 'H'

def __query(qt, x, y) :
	n, get_coords = qt
	cx = (n.extent.l + n.extent.r) / 2
	cy = (n.extent.t + n.extent.b) / 2
	print here(), cx, cy
	hits = ([ (o, (n, _V)) for o in n.vertical if __within(get_coords(o), y=y) ] +
		[ (o, (n, _H)) for o in n.horizontal if __within(get_coords(o), x=x) ] )
	qi = __q_to_i[x < cx, y < cy]
	if n.quads[qi] != None :
		return hits + __query((n.quads[qi], get_coords), x, y)
	else :
		return hits

def qtree_query(qt, x, y) :
	hits = __query(qt, x, y)
#	print hits
	return [ o for o, _ in hits ]

def __gc_node(n) :
	if ((len(n.vertical) + len(n.horizontal)) == 0 and
			all([ q is None for q in n.quads ])) :
#		print here(), n.parent_node.quads
		if n.parent_node is not None :
			n.parent_node.quads[n.parent_quad] = None
			__gc_node(n.parent_node)

def qtree_remove(qt, o) :
	root, get_coords = qt
	o_l, o_t, o_r, o_b = get_coords(o)
	hits = __query(qt, (o_l+o_r)/2, (o_t+o_b)/2)
	for o_found, (n, lst) in hits :
		if o == o_found :
			assert(lst in (_V, _H))
			if lst == _V :
				n.vertical.remove(o)
			elif lst == _H :
				n.horizontal.remove(o)
			__gc_node(n)


#def qtree_contains(qt, x, y) :
#	return []


if __name__ == "__main__" :
	qt = qtree_init(2000, 2000, get_obj_coords=lambda o: o[1])
	o0 = ("o0", _rect_t(10, 10, 50, 50))
	qtree_insert(qt, o0)
	print here(), qtree_query(qt, 666, 667)
	print here(), qtree_query(qt, 11, 11)
	qtree_remove(qt, o0)
	print here(), qtree_query(qt, 11, 11)
	qtree_insert(qt, o0)
	print here(), qtree_query(qt, 11, 11)


