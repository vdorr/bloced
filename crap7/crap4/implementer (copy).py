
from dfs import *
from collections import namedtuple
from functools import partial
from itertools import groupby, chain, product
from pprint import pprint

# 1) preprocess :
#	- expand macroes
#	- convert joints to connections
#	- check consistency (i/o directions)
# 2) separate connected components
# 3) check for implicit feedback paths
# 4) optimize stateless and/or constant partitions
# 5) perform minimal-edge-overlap(tm) topological sort
# 6) export :
#	- graph for generator
#	- inputs and outputs for verifier

# ------------------------------------------------------------------------------------------------------------

#	model :
#	( from_block, from_term ) : [ ( to_block0, to_term0, ), ... ]

# ------------------------------------------------------------------------------------------------------------

impl_t = namedtuple("implementation", ["graph", "cycles", "looseends"])
adjs_t = namedtuple("a", [ "p", "s", ])

# ------------------------------------------------------------------------------------------------------------

from generator import codegen

def implement_dfs(model, meta) :
	g0, conns = __preproc(model, meta)
	#gcomps = __components(g0)
	gsorted = [ __tsort(__graph_part(g0, comp)) for comp in __components(g0) ]
	#print("sorted"); pprint(gsorted)

	
	print codegen(g0, conns, list(chain(*gsorted)))

	return impl_t(None, None, None)

# ------------------------------------------------------------------------------------------------------------

def __graph_part(g, comp) :
	return dict(map(lambda v: (v, g[v]), comp))

# ------------------------------------------------------------------------------------------------------------

# TODO add termination condition based on return value of f()
def __ubft_int(g, v, f, visited) :
	adjlst = g[v]
	vtcs = adjlst.p.union(adjlst.s) - visited
	visited.update(vtcs)
	visit = list(vtcs)
	#print "to be visited from", v, visit
	for vt in visit :
		f(vt)
	for vt in visit :
		__ubft_int(g, vt, f, visited)

def __ubft(g, v, f) :
	visited = set([v])
	__ubft_int(g, v, f, visited)
	#print visited

# ------------------------------------------------------------------------------------------------------------

def __components_visitor(blocks, comp, vt) :
	if vt in blocks :
		blocks.remove(vt);
		comp.append(vt)

def __components(g) :
	blocks = list(g.keys())
	components = []
	while blocks :
		v = blocks.pop()
		comp = [ v ]
		__ubft(g, v, partial(__components_visitor, blocks, comp))
		if comp :
			components.append(comp)
	return components

# ------------------------------------------------------------------------------------------------------------

def __check_directions(conns) :
	return reduce(lambda x, item: x and item[0][1].direction == OUTPUT_TERM and
		reduce(lambda y, inp: y and inp[1].direction == INPUT_TERM, item[1], True),
			conns.items(), True)

# ------------------------------------------------------------------------------------------------------------

def __expand_joints(g) :
	graph = dict(g)
	joints = filter(lambda i: isinstance(i[0].prototype, JointProto), g.items())
	for j in joints :
		p, s = graph.pop(j[0])
		for v in p :
			graph[v].s.remove(j[0])
			graph[v].s.update(s)
		for v in s :
			graph[v].p.remove(j[0])
			graph[v].p.update(p)
	return graph

# ------------------------------------------------------------------------------------------------------------

def __check_implicit_cycles(g) :
	pass

# ------------------------------------------------------------------------------------------------------------

def __tsort(g) :
	#return __tsort_easy(g)
	#return __tsort_mkII(g)
	return __tsort_dft(g)

# ------------------------------------------------------------------------------------------------------------

def __no_preds(p) :
	return reduce(lambda x, pre: x and isinstance(pre, DelayProto), p, True)

def __tsort_easy(graph) :
	g = dict(graph)
	sort = []
	while g :
		inputs = filter(lambda i: __no_preds(i[1].p), g.iteritems())
		for v, adjacent in inputs :
			p, s = g.pop(v)
			sort.append(v)
			for v_succ in s :
				g[v_succ].p.remove(v)
	return sort

def __tsort_dive(g, v, sort, sorted_parts) :
	p, s = g.pop(v)
	sort.append(v)
	for v_succ in s :
		p = g[v_succ].p
		p.remove(v)
		if __no_preds(p) :
			#sort.append(v_succ)
			__tsort_dive(g, v_succ, sort)
		else :
			# take partial sort and store fo future use
			# sorted_parts[v_succ] = (partial_)sort #XXX
			pass

def __tsort_mkII(graph) :
	g = dict(graph)

	# vertex_on_which_dive_stopped : partial sort
	sorted_parts = {}

	sort = []
	while g :
		inputs = filter(lambda i: __no_preds(i[1].p), g.iteritems())
		for v, adjacent in inputs :
			__tsort_dive(g, v, sort, sorted_parts)
	return sort

def __tsort_dft_visit(g, n, l, visited) :
	#if n has not been visited yet then
	if not n in visited :
		#mark n as visited
		visited.append(n)
		#for each node m with an edge from n to m do
		for m in g[n].s :
			#visit(m)
			__tsort_dft_visit(g, m, l, visited)
		#add n to L
		l.append(n)

def __tsort_dft(graph) :
	g = dict(graph)

	# L <- Empty list that will contain the sorted nodes
	l = []
	#S <- Set of all nodes with no incoming edges
	s = map(lambda itm: itm[0], filter(lambda i: __no_preds(i[1].p), g.iteritems()))

	visited = []

	#for each node n in S do
	for n in s :
		#visit(n)
		ll = []
		__tsort_dft_visit(graph, n, ll, visited)
		#print "ll=", ll
		l += ll

	l.reverse()
	return l

# ------------------------------------------------------------------------------------------------------------

def __preproc(model, meta) :
	blocks = model.get_blocks()
	conns = dict(filter(lambda item: item[1], model.get_connections().items()))
	#print("conns"); pprint(conns)

	for v in filter(lambda b: isinstance(b.prototype, DelayProto), blocks) :
		blocks.pop()
		inp = BlockModel(__DelayInProto())
		outp = BlockModel(__DelayOutProto())
		

	print("__check_directions1:", __check_directions(conns))
	
	s_dal = map(lambda g: (g[0],
		set(reduce(lambda a, i: a + map(lambda l: l[0], i[1]), g[1], [])) ),
		groupby(conns.items(), lambda x: x[0][0]))
	succs = sorted(s_dal + map(lambda v: (v, set([])), list(set(blocks)-set(map(lambda x: x[0], s_dal)))))
	#print("succs"); pprint(succs)
	
	# successors: expand g to one-to-one mapping, swap mappings and apply function above
	
	
#	pprint(list(groupby(reduce(lambda a, i: chain(a, product(i[1], [i[0]])), succs, []), lambda x: x[0])))

	rv = sorted(reduce(lambda a, i: chain(a, product(i[1], [i[0]])), succs, []))
	#print "rv"; pprint(rv)
	#pgrps = groupby(rv, lambda x: x[0])

	#print "pgrps"; pprint(pgrps)
	#pgrps2 = map(lambda g: (g[0], set(list(g[1])) ), pgrps)
	pgrps2 = []
	for k, g in groupby(rv, lambda x: x[0]) : #TODO use comprehension
		pgrps2.append((k, [ i for i in g ]))
#		itm = []
#		for i in g :
#			itm.append(i) #TODO use comprehension, eliminate itm entirely
#		pgrps2.append((k, itm))

	#print "pgrps2"; pprint(pgrps2)
	
	p_dal = map(lambda g: (g[0], set(map(lambda v: v[1], g[1])) ), pgrps2)
	
	#print("p_dal"); pprint(p_dal)	
	preds = p_dal + map(lambda v: (v, set([])), list(set(blocks) - set(map(lambda x: x[0], p_dal))))
	#print "preds"; pprint(preds)
	
	preds_dict = dict(preds)
	#print("preds_dict"); pprint(preds_dict)
	g = dict(map(lambda i: (i[0], adjs_t(preds_dict[i[0]], i[1])), succs)) # this is our graph
	#print("g"); pprint(g)

	g2 = __expand_joints(g)
	#print("joints expanded"); pprint(g2)
	print("__check_directions2:", __check_directions(conns))

	pprint(g)
	pprint(conns)
	return None

	return g, conns

# ------------------------------------------------------------------------------------------------------------

