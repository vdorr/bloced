
from dfs import *
from collections import namedtuple
from functools import partial
from itertools import groupby, chain, product, ifilter
from pprint import pprint
from sys import exit

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

def __expand_joints(g) :
	graph = dict(g)
	joints = filter(lambda i: isinstance(i[0].prototype, JointProto), g.items())
	print "__expand_joints-graph-pre"; pprint(graph)
	print "__expand_joints"; pprint(joints)
	for j in joints : #ifilter(lambda i: isinstance(i[0].prototype, JointProto), g.items()) :
		p, s = graph.pop(j[0])
		for v in p :
			graph[v].s.remove(j[0])
			graph[v].s.update(s)
		for v in s :
			graph[v].p.remove(j[0])
			graph[v].p.update(p)
	print "__expand_joints-graph-post"; pprint(graph)
	return graph

# ------------------------------------------------------------------------------------------------------------

def __preproc(model, meta) :
	blocks = model.get_blocks()
	conns = dict(filter(lambda item: item[1], model.get_connections().iteritems()))
	#print("conns"); pprint(conns)

	delays_numbering = 0
	for v in ifilter(lambda b: isinstance(b.prototype, DelayProto), blocks) :
		blocks.remove(v)
		inp = BlockModel(DelayInProto())
		inp.nr = delays_numbering
		outp = BlockModel(DelayOutProto())
		outp.nr = delays_numbering
		++delays_numbering
		blocks += [ inp, outp ]
		for k, val in ifilter(lambda i: i[0][0] == v, conns.iteritems()) :
			print "!!!", (k, val)
			conns.pop(k)
			conns[outp, outp.get_terms()[0]] = val
		#filter(lambda i: reduce(i[1]) == v, conns.itemiter())
		xxx = ifilter(lambda i: reduce(lambda a, x: a or x[0] == v, i[1], False), conns.iteritems())
		for k, val in xxx :
			print "delay replace", k, val
			#conns[k] = map(lambda x: (inp, inp.get_terms()[0]) if x[0] == v else x, val)
			conns[k] = map(lambda x: (inp, inp.get_terms()[0]) if x[0] == v else x, val)

	return __preproc2(blocks, conns)

def __to_dict_of_lists(it, key_selector, value_grouper) :
	pass#return dict(map(lambda))

def groupby_to_dict(it, key_selector, value_selector, value_grouper) :
	return dict(
		[ (key, value_grouper([ value_selector(val) for val in values ])) 
			for key, values in groupby(sorted(it), key_selector) ])

def __preproc2(blocks, conns) :
	
	print "conns:"; pprint(conns)
	print "blocks", pprint(blocks)
#	return None

	print("__check_directions1:", __check_directions(conns))

	s_dal = map(lambda g: (g[0],
		set(reduce(lambda a, i: a + map(lambda l: l[0], i[1]), g[1], [])) ),
		groupby(sorted(conns.items()), lambda x: x[0][0]))
#	print("s_dal"); pprint(s_dal)
	succs = list(sorted(
		s_dal + map(lambda v: (v, set([])), list(set(blocks)-set(map(lambda x: x[0], s_dal))))))



	s_adjl = groupby_to_dict(conns.items(),
		lambda i: i[0][0],			# group connections by blocks
		lambda i: [ v for v, t in i[1] ],	# select successor blocks as values
		lambda values: set(chain(*values)))	# pack lists of successor blocks into sets

	sinks = ifilter(lambda v: not v in s_adjl, blocks) # append sink and orphaned blocks
	s_adjl.update([ (v, set()) for v in sinks ])

#	print("groupby_to_dict"); pprint(s_adjl)
	
	succs = s_adjl.items() #XXX XXX XXX

#	print("succs"); pprint(succs)
	
	# successors: expand g to one-to-one mapping, swap mappings and apply function above
	
	
#	pprint(list(groupby(reduce(lambda a, i: chain(a, product(i[1], [i[0]])), succs, []), lambda x: x[0])))

	rv = list(sorted(reduce(lambda a, i: chain(a, product(i[1], [i[0]])), succs, [])))
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

	print "pgrps2"; pprint(pgrps2)
	
	p_dal = map(lambda g: (g[0], set(map(lambda v: v[1], g[1])) ), pgrps2)
	
	#print("p_dal"); pprint(p_dal)	
	preds = p_dal + map(lambda v: (v, set([])), list(set(blocks) - set(map(lambda x: x[0], p_dal))))
	#print "preds"; pprint(preds)
	
	preds_dict = dict(preds)
	#print("preds_dict"); pprint(preds_dict)
	g = dict(map(lambda i: (i[0], adjs_t(preds_dict[i[0]], i[1])), succs)) # this is our graph
#	g = {}
#	for v in succs 
	
	
	
	#print("g"); pprint(g)

	g2 = __expand_joints(g)
	#print("joints expanded"); pprint(g2)
	print("__check_directions2:", __check_directions(conns))


	conns2 = dict(ifilter(lambda c: not isinstance(c[0][0].prototype, JointProto), conns.iteritems()))

	print "graph",  pprint(g)
	print "conns2",  pprint(conns2)
#	return None
#	exit(666)

	return g, conns2

# ------------------------------------------------------------------------------------------------------------

