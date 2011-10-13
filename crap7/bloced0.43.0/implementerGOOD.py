
from dfs import *
from collections import namedtuple
from functools import partial
from itertools import groupby, chain, product, ifilter, izip, count, imap
from pprint import pprint
import sys
from generator import codegen

# ------------------------------------------------------------------------------------------------------------

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
	pass #TODO

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

def __expand_joints(g, connections) :
	graph = dict(g)
	conns = dict(connections)
	joints = filter(lambda i: isinstance(i[0].prototype, JointProto), g.iteritems())
	#print "__expand_joints-graph-pre"; pprint(graph)
	#print "__expand_joints"; pprint(joints)
	for j in joints : #TODO ifilter(lambda i: isinstance(i[0].prototype, JointProto), g.iteritems()) :

		p, s = graph.pop(j[0])

		#joint_out_terms = filter(lambda t: t.direction == OUTPUT_TERM, j[0].terms)
		
		#TODO make it set again
		j_succs = list(set(chain(
			*[ dst for src, dst in filter(lambda i: i[0][0] == j[0], conns.iteritems()) ])))

		joint_in_terms = filter(lambda t: t.direction == INPUT_TERM, j[0].terms)
		assert len(joint_in_terms) == 1

		for v in p :
			graph[v].s.remove(j[0])
			graph[v].s.update(s)
			
			# edges leading to joint
			eltj = ifilter(lambda term: term.direction == OUTPUT_TERM and (v, term) in conns,
				v.terms)
			for t in eltj :
				# replace joint in vs succs with joints successors
				conns[v, t].remove((j[0], joint_in_terms[0]))
				conns[v, t] += j_succs #XXX XXX XXX beware of duplicities!!!
				#conns[v, t].update(j_succs)

		for v in s :
			graph[v].p.remove(j[0])
			graph[v].p.update(p)

#			for t in joint_out_terms :
#				conns[j, t].remove(
#				graph[v].s.update(s)

#XXX	conns2 = dict(ifilter(lambda c: not isinstance(c[0][0].prototype, JointProto), conns.iteritems()))

	#print "__expand_joints-graph-post"; pprint(graph)
	return graph, dict(ifilter(lambda c: not isinstance(c[0][0].prototype, JointProto), conns.iteritems()))

# ------------------------------------------------------------------------------------------------------------

def groupby_to_dict(it, key_selector, value_selector, value_grouper) :
	return dict(
		[ (key, value_grouper([ value_selector(val) for val in values ])) 
			for key, values in groupby(sorted(it), key_selector) ])

# ------------------------------------------------------------------------------------------------------------

def reverse_dict_of_lists(d, key_grouper) :
	return groupby_to_dict(
		chain(*[ product(v, [k]) for k, v in d.iteritems() ]),
		lambda i: i[0], lambda i: i[1], key_grouper)

# ------------------------------------------------------------------------------------------------------------

def dict_map(d, k_map, v_map, item_filter=lambda k,v: True) :
	return dict(
		imap(lambda i: (k_map(*i), v_map(*i)),
			ifilter(lambda i: item_filter(*i), d.iteritems())))

# ------------------------------------------------------------------------------------------------------------

def __expand_delays(blocks, conns) :

	delays = set(ifilter(lambda b: isinstance(b.prototype, DelayProto), blocks))

	expddel_t = namedtuple("expddel_t", ["i", "o"])
	def __expddel(nr) :
		i = BlockModel(DelayInProto(), None)
		o = BlockModel(DelayOutProto(), None)
		i.nr = o.nr = nr
		#TODO return expddel_t((i, i.terms[0]), (o, o.terms[0]))
		return expddel_t(i, o)

	expd = dict([ (delay, __expddel(nr)) for delay, nr in izip(delays, count()) ])

	conns2 = dict_map(conns,
		lambda k, v: (
			(expd[k[0]].o, expd[k[0]].o.terms[0])#expd[k[0]].o
			if isinstance(k[0].prototype, DelayProto)
			else k
		),
		lambda k, values: [
			(expd[b].i, expd[b].i.terms[0])#expd[k[0]].i
			if isinstance(b.prototype, DelayProto)
			else (b, t)
				for b, t in values
		])

	return list((set(blocks)-delays).union(chain(*expd.itervalues()))), conns2, expd
#	return list((set(blocks)-delays).union(chain(*[ (i[0], o[0]) for i, o in expd.itervalues() ]))), conns2

# ------------------------------------------------------------------------------------------------------------

def __preproc(model, meta) :
	blocks0 = model.blocks
	conns0 = dict(ifilter(lambda item: item[1], model.connections.iteritems()))

	blocks, conns, delays = __expand_delays(blocks0, conns0)

	assert(__check_directions(conns))

	s_adjl = groupby_to_dict(conns.iteritems(),
		lambda i: i[0][0],			# group connections by blocks
		lambda i: [ v for v, t in i[1] ],	# select successor blocks as values
		lambda values: set(chain(*values)))	# pack lists of successor blocks into sets
	sinks = ifilter(lambda v: not v in s_adjl, blocks) # append sink and orphaned blocks
	s_adjl.update([ (v, set()) for v in sinks ])

	pprint(s_adjl)
	sys.exit(0)


	preds = reverse_dict_of_lists(s_adjl, lambda values: set(values))
	succs = s_adjl.iteritems() #TODO iteritems

	g = dict(
		[ (k, adjs_t(preds[k] if k in preds else set(), v))
			for k, v in succs ] )

	g2, conns2 = __expand_joints(g, conns)

	assert(__check_directions(conns2))

	return g2, conns2, delays

# ------------------------------------------------------------------------------------------------------------

def implement_dfs(model, meta) :
	g0, conns, delays = __preproc(model, meta)
	#gcomps = __components(g0)
	gsorted = [ __tsort(__graph_part(g0, comp))
		for comp in __components(g0) ]
	
	print codegen(g0, conns, delays, list(chain(*gsorted)))

	return impl_t(None, None, None)

# ------------------------------------------------------------------------------------------------------------

if __name__ == "__main__" :
#	import argparse
#	parser = argparse.ArgumentParser(description="bloced")
#	parser.add_argument("file", metavar="fname", type=str, nargs=1,
#                   help="input file")
#	args = parser.parse_args()
#	fname = args.file[0]
	fname = sys.argv[1]
	from serializer import unpickle_dfs_model
	try :
		f = open(fname, "rb")
		model = unpickle_dfs_model(f)
		f.close()
	except IOError :
		print("IOError")
		exit(666)
	out = implement_dfs(model, None)
	#print "out:", out
	exit(0)


# ------------------------------------------------------------------------------------------------------------

