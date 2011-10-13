
from dfs import *
from collections import namedtuple
from functools import partial
from itertools import groupby, chain, product, ifilter, izip, count, imap
from pprint import pprint
import sys

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
#	return dict(map(lambda v: (v, g[v]), comp))
	return { v: g[v] for v in comp }

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
	print("TODO: __check_implicit_cycles")

# ------------------------------------------------------------------------------------------------------------

def __tsort(g) :
	#return __tsort_easy(g)
	#return __tsort_mkII(g)
	return __tsort_dft(g)

# ------------------------------------------------------------------------------------------------------------

def __no_preds(p) :
	return reduce(lambda x, pre: x and isinstance(pre, DelayProto), p, True)

def __no_succs(s) :
	return reduce(lambda x, succ: x and isinstance(succ, DelayProto), s, True)

# ------------------------------------------------------------------------------------------------------------

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

def __dft_p_sorter(g, conns, preds) :
	for v in preds :
		yield v

def __dft_dive(g, conns, n, pre_visit, post_visit, visited) :
	if not n in visited :
		visited.append(n)
		pre_visit(n)
		for m in __dft_p_sorter(g, conns, g[n].p) : #g[n].p :
			__dft_dive(g, conns, m, pre_visit, post_visit, visited)
		post_visit(n)

def dft(g, conns, pre_visit, post_visit, pre_tree, post_tree) :
	s = [ v for v, neighbours in g.items() if __no_succs(neighbours.s) ]#TODO choose between inputs and outputs
	visited = []
	for v in s :
		pre_tree(v)
		__dft_dive(g, conns, v, pre_visit, post_visit, visited)
		post_tree(v)

# ------------------------------------------------------------------------------------------------------------

def __dft_alt_p_sorter(g, preds) :
	for v in preds :
		yield v

def __dft_alt_dive(g, n, pre_visit, post_visit, visited) :
	if not n in visited :
		visited.append(n)
		pre_visit(n)
		for m in __dft_alt_p_sorter(g, g[n].p) : #g[n].p :
			__dft_alt_dive(g, m, pre_visit, post_visit, visited)
		post_visit(n)

def dft_alt(g, pre_visit, post_visit, pre_tree, post_tree, sinks_to_sources=True) :
	s = [ v for v, (p, s) in g.items() if not ( s if sinks_to_sources else p ) ]
	visited = [] #XXX what about dictionary? should be faster
	for v in s :
		pre_tree(v)
		__dft_dive(g, v, pre_visit, post_visit, visited)
		post_tree(v)

# ------------------------------------------------------------------------------------------------------------

def dft_norecurse(g, pre_visit, post_visit) :
	pass #TODO

# ------------------------------------------------------------------------------------------------------------

def groupby_to_dict(it, key_selector, value_selector, value_grouper) :
#	return dict(
#		[ (key, value_grouper([ value_selector(val) for val in values ])) 
#			for key, values in groupby(sorted(it, key=key_selector), key_selector) ])

	return { key : value_grouper([ value_selector(val) for val in values ])
			for key, values in groupby(sorted(it, key=key_selector), key_selector) }

# ------------------------------------------------------------------------------------------------------------

def reverse_dict_of_lists(d, key_grouper) :
#	return groupby_to_dict(
#		chain(*[ product(v, [k]) for k, v in d.iteritems() ]),
#		lambda i: i[0], lambda i: i[1], key_grouper)
#	l = list(chain(*[ product(v, [k]) for k, v in d.iteritems() ]))

	l = list(chain(*[ [ (v, k) for v in values ] for k, values in d.items() ]))

#	pprint(l)
#	sys.exit(0)

	return groupby_to_dict(l, lambda i: i[0], lambda i: i[1], key_grouper)

# ------------------------------------------------------------------------------------------------------------

def dict_map(d, k_map, v_map, item_filter=lambda k,v: True) :
#	return dict(
#		imap(lambda i: (k_map(*i), v_map(*i)),
#			ifilter(lambda i: item_filter(*i), d.iteritems())))
	return { k_map(*i): v_map(*i) for i in d.items() if item_filter(*i) }

# ------------------------------------------------------------------------------------------------------------

def __expand_joints(g, connections) :
	graph = dict(g)
	conns = dict(connections)
#	joints = filter(lambda i: isinstance(i[0].prototype, JointProto), g.iteritems())
	joints = [ i for i in g.items() if isinstance(i[0].prototype, JointProto) ]
	assert(joints == filter(lambda i: isinstance(i[0].prototype, JointProto), g.iteritems()))

	#print "__expand_joints-graph-pre"; pprint(graph)
	#print "__expand_joints"; pprint(joints)
	for j in joints : #TODO ifilter(lambda i: isinstance(i[0].prototype, JointProto), g.iteritems()) :

		p, s = graph.pop(j[0])

		#joint_out_terms = filter(lambda t: t.direction == OUTPUT_TERM, j[0].terms)
		
		#TODO make it set again
#		j_succs = list(set(chain(
#			*[ dst for src, dst in filter(lambda i: i[0][0] == j[0], conns.iteritems()) ])))
		j_succs = list(set(chain(*[ dst for src, dst in conns.items() if  src[0] == j[0] ])))#TODO make it set again
		assert(j_succs == list(set(chain(*[ dst for src, dst in filter(lambda i: i[0][0] == j[0], conns.items()) ]))))

#		joint_in_terms = filter(lambda t: t.direction == INPUT_TERM, j[0].terms)
		joint_in_terms = [ t for t in j[0].terms if t.direction == INPUT_TERM ]
		assert(joint_in_terms == filter(lambda t: t.direction == INPUT_TERM, j[0].terms))
		assert len(joint_in_terms) == 1

		for v in p :
			graph[v].s.remove(j[0])
			graph[v].s.update(s)
			
			# edges leading to joint
#			eltj = ifilter(lambda term: term.direction == OUTPUT_TERM and (v, term) in conns,
#				v.terms)
			eltj = [ term for term in v.terms if term.direction == OUTPUT_TERM and (v, term) in conns ]
			assert(eltj == filter(lambda term: term.direction == OUTPUT_TERM and (v, term) in conns, v.terms))
			for t in eltj :
				# replace joint in vs succs with joints successors
				conns[v, t].remove((j[0], joint_in_terms[0]))
				conns[v, t] += j_succs #XXX XXX XXX beware of duplicities!!!
				#conns[v, t].update(j_succs)

		for v in s :
			graph[v].p.remove(j[0])
			graph[v].p.update(p)

#			for t in joint_out_terms :
#				conns[j, t].remove((expd[k[0]].o, expd[k[0]].o.terms[0])
#			if isinstance(k[0].prototype, JointProto)
#			else k
#				graph[v].s.update(s)

#XXX	conns2 = dict(ifilter(lambda c: not isinstance(c[0][0].prototype, JointProto), conns.iteritems()))

	#print "__expand_joints-graph-post"; pprint(graph)
#	return graph, dict(ifilter(lambda c: not isinstance(c[0][0].prototype, JointProto), conns.iteritems()))
	conns_new = { k : v for k, v in conns.items() if not isinstance(k[0].prototype, JointProto) }
	assert(conns_new == dict(ifilter(lambda c: not isinstance(c[0][0].prototype, JointProto), conns.iteritems())))
	return graph, conns_new

# ------------------------------------------------------------------------------------------------------------

#TODO implement
#TODO possibly use in dft
def __edges_iter(neighbours) :
	for st, dests in neighbours :
		for tb, tt in dests :
			yield (st, tb, tt)

def __cut_joint(g, j) :
	p, s = g.pop(j)

	assert(len(p) == 1 and len(p[0][1]) == 1) #single input term, single predeccessor

	j_term, ((pred_block, pred_term), ) = p[0]

	g[pred_block].s.ADD(s)

#	print "x:", j, j_term, pred_block, pred_term
#	pprint(p)
#	pprint(s)

	for st, dests in s :
		for tb, tt in dests :
		graph[tb].p = [ ? for ?? in ?!? if 666 ]

#	for st, tb, tt in __edges_iter(p) :
#		print "\tp:", st, tb, tt
#		graph[v].s.remove(j[0])
#		graph[v].s.update(s)

#	for st, tb, tt in __edges_iter(s) :
#		print "\ts:", st, tb, tt
	

def __expand_joints_new(g) :

	joints = [ b for b, _ in g.items() if isinstance(b.prototype, JointProto) ]

	graph = dict(g)

	#XXX is there a way how to do it functionally?
	for j in joints :
		__cut_joint(graph, j)

#		p, s = graph.pop(j)

#		j_succs = list(set(chain(*[ dst for (sb, st), dst in conns.items() if sb == j ])))

#		j_input_terms = [ t for t in j.terms if t.direction == INPUT_TERM ]
#		assert(len(j_input_terms) == 1)
#		j_input, = j_input_terms 

#		for v in p :
#			graph[v].s.remove(j)
#			graph[v].s.update(s)
#			
#			# edges leading to joint
#			eltj = [ t for t in v.terms if t.direction == OUTPUT_TERM and (v, t) in conns ]

#			for t in eltj :
#				# replace joint in vs succs with joints successors
#				conns[v, t].remove((j, j_input))
#				conns[v, t] += j_succs #XXX XXX XXX beware of duplicities!!!

#		for v in s :
#			graph[v].p.remove(j)
#			graph[v].p.update(p)

#	conns_new = { k : v for k, v in conns.items() if not isinstance(k[0].prototype, JointProto) }

#	return graph, conns_new

# ------------------------------------------------------------------------------------------------------------

def __expand_delays(blocks, conns) :

#	delays = set(ifilter(lambda b: isinstance(b.prototype, DelayProto), blocks))
	delays = { b for b in blocks if isinstance(b.prototype, DelayProto) }

	expddel_t = namedtuple("expddel_t", ["i", "o"])
	def __expddel(nr) :
		i = BlockModel(DelayInProto(), None)
		o = BlockModel(DelayOutProto(), None)
		i.nr = o.nr = nr
		#TODO return expddel_t((i, i.terms[0]), (o, o.terms[0]))
		return expddel_t(i, o)

#	expd = dict([ (delay, __expddel(nr)) for delay, nr in izip(delays, count()) ])
	expd = { delay : __expddel(nr) for delay, nr in zip(delays, count()) }

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

#def groupbytoset(it, keyfunc) :
#	d = {}
#	for i in it :
#		k = keyfunc(i)
#		if not key in d :
#			d[k] = set()
#		d[k].add(i)

# ------------------------------------------------------------------------------------------------------------

#def __predecessors(d) :

##	l = sorted(chain(*[ [ (v, k) for v in values ] for k, values in d.items() ]), key=lambda kv: kv[0])
#	l = list(chain(*[ [ (k, v) for v in values ] for k, values in d.items() ]))
##	print("d")
##	pprint(d)
##	print("l")
##	pprint(l)
##	sys.exit(0)
#	d = {}
#	for v, k in l :
##		print "v, k", v, k
#		if not k in d :
#			d[k] = set()
#		d[k].add(v)

##	print("d")
##	pprint(d)
##	sys.exit(0)
#	return d

#def yyyy(values) :
#	pprint(values)
#	return set(values)

def __make_dag(model, meta) :
	blocks0 = model.blocks #XXX what?
#	conns0 = dict(ifilter(lambda item: item[1], model.connections.iteritems()))
#	print("conns0")
#	pprint(conns0)

	conns0 = { k : v for k, v in model.connections.items() if v } #XXX what?
#	print("conns0")
#	pprint(conns0)
#	sys.exit(0)

	blocks, conns, delays = __expand_delays(blocks0, conns0)
#	print("blocks")
#	pprint(blocks)
#	sys.exit(0)

	assert(__check_directions(conns))

	s_adjl = groupby_to_dict(conns.items(),
		lambda i: i[0][0],			# group connections by blocks
		lambda i: [ v for v, t in i[1] ],	# select successor blocks as values
		lambda values: set(chain(*values)))	# pack lists of successor blocks into sets

#	sinks = list(ifilter(lambda v: not v in s_adjl, blocks)) # append sink and orphaned blocks

#	sinks = [ v for v in blocks if not v in s_adjl ] # append sink and orphaned blocks
#	s_adjl.update([ (v, set()) for v in sinks ])
	s_adjl.update([ (v, set()) for v in blocks if not v in s_adjl ])

#	pprint(s_adjl)
#	sys.exit(0)

#	preds = __predecessors(s_adjl)
#	preds = reverse_dict_of_lists(s_adjl, yyyy)
	preds = reverse_dict_of_lists(s_adjl, lambda values: set(values))
#	succs = s_adjl.iteritems()

#	lambda values: set(values))
#	succs = s_adjl.iteritems() #TODO iteritems

#	pprint(preds)
#	sys.exit(0)

#	g = dict(
#		[ (k, adjs_t(preds[k] if k in preds else set(), v))
#			for k, v in s_adjl.items() ] )
	g = { k : adjs_t(preds[k] if k in preds else set(), v)
			for k, v in s_adjl.items() }

#	print "g"
#	pprint(g)
#	sys.exit(0)

	g2, conns2 = __expand_joints(g, conns)

	assert(__check_directions(conns2))

	return g2, conns2, delays

# ------------------------------------------------------------------------------------------------------------

def __in_terms(terms) :
	return [ t for t in terms if t.direction == INPUT_TERM  ]

def __out_terms(terms) :
	return [ t for t in terms if t.direction == OUTPUT_TERM  ]

#def __adj_edges(b, conns, neighbours) :
#	inputs
#	outputs

def __adj_in_edges(b, conns, neighbours) :
#	preds = reverse_dict_of_lists(s_adjl, lambda values: set(values))
	print b, "inputs:", __in_terms(b.prototype.terms)

def __adj_out_edges(b, conns, neighbours) :
#	print b, neighbours
	print b, "outputs:", __out_terms(b.prototype.terms)
#	return { st : dst for (sb, st), dst in conns.items() if src[0] in neighbours }

def __merge_g_and_conns(g, conns) :
	return { b : adjs_t(__adj_in_edges(b, conns, p), __adj_out_edges(b, conns, s)) for b, (p, s) in g.items() }

# ------------------------------------------------------------------------------------------------------------

##def single(l) :
##	if len(l) != 1 :
##		raise Exception("not single element in list")
##	return l[0]

#def __expand_joints_alt(blocks, conns) :

#	joints = { b for b in blocks if isinstance(b.prototype, JointProto) }
#	
#	expd = { joint : __expddel(nr) for joint, nr in zip(delays, count()) }

#	conns2 = dict_map(conns,
#		lambda k, v: (
#			(expd[k[0]].o, expd[k[0]].o.terms[0])
#			if isinstance(k[0].prototype, JointProto)
#			else k
#		),
#		lambda k, values: [
#			(expd[b].i, expd[b].i.terms[0])
#			if isinstance(b.prototype, JointProto)
#			else (b, t)
#				for b, t in values
#		])

##	conns2 = { (expd[k[0]].o, expd[k[0]].o.terms[0])
##			if isinstance(k[0].prototype, JointProto)
##			else k
##	:
## [
##			(expd[b].i, expd[b].i.terms[0])
##			if isinstance(b.prototype, JointProto)
##			else (b, t)
##				for b, t in values

##			for k, v in conns.items() }

#	return list(set(blocks)-joints), conns2, expd

# ------------------------------------------------------------------------------------------------------------

#TODO	__check_directions(conns)
def __make_dag_alt(model, meta) :

	conns0 = { k : v for k, v in model.connections.items() if v }
	blocks, conns1, delays = __expand_delays(model.blocks, conns0)

#	conns = { k : single(v) for k, v in model.connections.items() if v }
#	conns = { k : single(v) for k, v in conns1.items() if v }
#	pprint(conns)
#	sys.exit(0)

	conns_rev = reverse_dict_of_lists(conns1, lambda values: list(set(values)))
#	pprint(conns_rev)
#	sys.exit(0)

##[ i for i in conns.items() if ]
	

#		[ (sb, st) for ((sb, st), (tb, tt)) in conns0.items() ]

#	tb_t = namedtuple("port", ["b", "t"])

	graph = { b : adjs_t(
			[ (t, conns_rev[(b, t)] if (b, t) in conns_rev else []) for t in __in_terms(b.terms) ],
			[ (t, conns1[(b, t)] if (b, t) in conns1 else []) for t in __out_terms(b.terms) ])
		for b in blocks }
	
	__expand_joints_new(graph)

#	pprint(graph)
	sys.exit(0)
#	return graph




#	s_adjl = groupby_to_dict(conns.items(),
#		lambda i: i[0][0],			# group connections by blocks
#		lambda i: [ v for v, t in i[1] ],	# select successor blocks as values
#		lambda values: set(chain(*values)))	# pack lists of successor blocks into sets

#	s_adjl.update([ (v, []) for v in blocks if not v in s_adjl ])

#	preds = reverse_dict_of_lists(s_adjl, lambda values: set(values))

#	g = { k : adjs_t(preds[k] if k in preds else set(), v)
#			for k, v in s_adjl.items() }

#	g2, conns2 = __expand_joints(g, conns)

#	return g2, conns2, delays

# ------------------------------------------------------------------------------------------------------------

def implement_dfs(model, meta, codegen) :

#	from fcodegen import codegen

	g, conns, delays = __make_dag(model, meta)

##	pprint(conns)
	graph = __make_dag_alt(model, meta)
	pprint(graph)
	sys.exit(0)

#	print g
#	print ""
#	print conns
#	print ""
#	print delays
#	print ""
	#gcomps = __components(g)
	gsorted = [ __tsort(__graph_part(g, comp))
		for comp in __components(g) ]
	
	print codegen(g, conns, delays, list(chain(*gsorted)))

	return impl_t(None, None, None)

# ------------------------------------------------------------------------------------------------------------

if __name__ == "__main__" :
#	import argparse
#	parser = argparse.ArgumentParser(description="bloced")
#	parser.add_argument("file", metavar="fname", type=str, nargs=1,
#                   help="input file")
#	args = parser.parse_args()
#	fname = args.file[0]
	from serializer import unpickle_dfs_model
	cgen = sys.argv[1]
	fname = sys.argv[2]
	if len(sys.argv) == 4 :
		pass#TODO use output file
	try :
		f = open(fname, "rb")
		model = unpickle_dfs_model(f)
		f.close()
	except :
		print("error loading input file")
		exit(666)
	import ccodegen
	import fcodegen
	cgens = {
		"c" : ccodegen.codegen,
		"f" : fcodegen.codegen,
	}
	out = implement_dfs(model, None, cgens[cgen])
	#print "out:", out
	exit(0)

# ------------------------------------------------------------------------------------------------------------

