
from dfs import *
from core import *
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

##TODO implement
##TODO possibly use in dft
#def __edges_iter(neighbours) :
#	for st, dests in neighbours :
#		for tb, tt in dests :
#			yield (st, tb, tt)

# ------------------------------------------------------------------------------------------------------------

#TODO TODO TODO

#def __neigbourhood_sanity_check(neigbourhood) :
#	pass

def __dag_structural_check(g, stop_on_first=True) :
# implicit feedback loops
# explicit feedback loops matching
	return False

def __dag_sanity_check(g, stop_on_first=True) :
# 1) dangling references (because of joints and macroes) :
#  a) terms in neigbourhood but not in prototype
#  b) the same as above for neigbours
#  c) blocks in neigbours but not in graph
#TODO matching predeccessors and successors lists
# 2) basic rules :
#  a) one predeccessor to input (equals unconnected inputs)
#  b) matching i/o directions
#TODO duplicities in neighbour lists
	for b, (p, s) in g.items() :
		for t, preds in p :
			if not t in b.prototype.terms :
				return (False, 0)
			if t.direction != INPUT_TERM :
				return (False, 1)
			if len(preds) != 1 :
				return (False, 2, (b, t, preds))
			for b_pred, t_pred in preds :
				if not b_pred in g :
					return (False, 3)
				if t_pred.direction != OUTPUT_TERM :
					return (False, 4)
				if not t_pred in b_pred.prototype.terms :
					return (False, 5)
		for t, succs in s :
			if not t in b.prototype.terms :
				return (False, 6)
			if t.direction != OUTPUT_TERM :
				return (False, 7)
			for b_succ, t_succ in succs :
				if not b_succ in g :
					return (False, 8)
				if t_succ.direction != INPUT_TERM :
					return (False, 9)
				if not t_succ in b_succ.prototype.terms :
					return (False, 10)
	return (True, )

#TODO TODO TODO

# ------------------------------------------------------------------------------------------------------------

def __neighbourhood_remove(neighbourhood, bt, block, term) :
	(neighbours, ) = [ succs for t, succs in neighbours if t == bt]
#	if (block, term) in neighbours :
	neighbours.remove((block, term))

def __neighbourhood_add(neighbourhood, bt, block, term) :
	(neighbours, ) = [ succs for t, succs in neighbours if t == bt]
	assert(not (block, term) in neighbours) # raise should be better
	neighbours.append((block, term))
	assert(len(neighbours)==1 if bt.direction == INPUT_TERM else True)

def __neighbourhood_safe_replace(neighbourhood, term, old_pair, new_pair) :
	(neighbours, ) = [ succs for t, succs in neighbourhood if t == term]
	if old_pair != None and old_pair in neighbours :
		neighbours.remove(old_pair)
	if new_pair != None and not new_pair in neighbours :
		neighbours.append(new_pair)

# ------------------------------------------------------------------------------------------------------------

#TODO TODO TODO

# to implement __expand_joints_new and macro expansion

#XXX because of symmetry, there should be only single map
# map_in = { old_term : [ (new_block, new term), ... ], ... }
# map_out = { old_term : (new_block, new term), ... }
def __replace_block_with_subgraph(g, n, subgraph, map_in, map_out) :
#	print "map_in=", map_in
#	print "map_out=", map_out

	p, s = g.pop(n)
	g.update(subgraph)

	npreds = dict(p)
	nsuccs = dict(s)

	for in_t, succs in map_in.items() :
		assert(in_t.direction == INPUT_TERM)
		((b_pred, t_pred),) = npreds[in_t]
		for b, t in succs :
			assert(t.direction == INPUT_TERM)
			assert(t_pred.direction == OUTPUT_TERM)
#			print b_pred, t_pred, "->", b, t
			#XXX something should be move outside this loop
#			__neighbourhood_safe_replace(neighbourhood, bt, old_pair, new_pair)
			__neighbourhood_safe_replace(g[b_pred].s, t_pred, (n, in_t), (b, t))
			__neighbourhood_safe_replace(g[b].p, t, None, (b_pred, t_pred))

	for out_t, (b, t) in map_out.items() :
		assert(out_t.direction == OUTPUT_TERM)
		assert(t.direction == OUTPUT_TERM)
		succs = nsuccs[out_t]
		for b_succ, t_succ in succs :
#			print b, t, "->", b_succ, t_succ
			assert(t_succ.direction == INPUT_TERM)
			__neighbourhood_safe_replace(g[b_succ].p, t_succ, (n, out_t), (b, t))
			__neighbourhood_safe_replace(g[b].s, t, None, (b_succ, t_succ))

	return None

#TODO TODO TODO

# ------------------------------------------------------------------------------------------------------------

#TODO generalize, use for consts etc
#XXX what about make this function clean and do dirty stuff only in __expand_joints
def __cut_joint(g, j) :
	p, s = g.pop(j)
	assert(len(p) == 1 and len(p[0][1]) == 1) #single input term AND single predeccessor
	j_term, ((pred_block, pred_term), ) = p[0]
	(pred_out_t, pred_succs), = [ (t, dests) for t, dests in g[pred_block].s if t == pred_term ]
	assert(len(pred_succs) == 1) #single successor - joint being removed
	pred_succs.remove((j, j_term))
	pred_succs += [ j_succ for _, (j_succ, ) in s ]
	for j_t, ((j_succ, j_succ_t), ) in s : # XXX maybe some generator instead of triple cycle?
		for pred_t, preds in g[j_succ].p :
			if pred_t == j_succ_t :
				for t, b in preds :
					preds.remove((t, b))
					preds.append((pred_block, pred_term))

def __cut_joint_alt(g, j) :
	(((it, ((pb, pt),)),), succs) = g[j]
	map_in = { it : [ (b, t) for (ot, ((b, t),)) in succs ] } # works only for joints!
	map_out = { out_term : (pb, pt) for out_term, _ in succs }
	__replace_block_with_subgraph(g, j, {}, map_in, map_out)

#XXX is there a way how to do it functionally?
def __expand_joints_new(g) :
#	joints = [ b for b, _ in g.items() if isinstance(b.prototype, JointProto) ]
	joints = [ b for b in g if isinstance(b.prototype, JointProto) ]
#	graph = dict(g)
	graph = g
	for j in joints :
#		__cut_joint(graph, j)
		__cut_joint_alt(graph, j)
#	printg(g)
#	print "__dag_sanity_check=", __dag_sanity_check(g)
#	sys.exit(0)

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

def __make_dag(model, meta) :
	blocks0 = model.blocks #XXX what?
#	conns0 = dict(ifilter(lambda item: item[1], model.connections.iteritems()))

	conns0 = { k : v for k, v in model.connections.items() if v } #XXX what?

	blocks, conns, delays = __expand_delays(blocks0, conns0)

	assert(__check_directions(conns))

	s_adjl = groupby_to_dict(conns.items(),
		lambda i: i[0][0],			# group connections by blocks
		lambda i: [ v for v, t in i[1] ],	# select successor blocks as values
		lambda values: set(chain(*values)))	# pack lists of successor blocks into sets

#	sinks = list(ifilter(lambda v: not v in s_adjl, blocks)) # append sink and orphaned blocks

#	sinks = [ v for v in blocks if not v in s_adjl ] # append sink and orphaned blocks
#	s_adjl.update([ (v, set()) for v in sinks ])
	s_adjl.update([ (v, set()) for v in blocks if not v in s_adjl ])

#	preds = __predecessors(s_adjl)
#	preds = reverse_dict_of_lists(s_adjl, yyyy)
	preds = reverse_dict_of_lists(s_adjl, lambda values: set(values))
#	succs = s_adjl.iteritems()

#	lambda values: set(values))
#	succs = s_adjl.iteritems() #TODO iteritems

#	g = dict(
#		[ (k, adjs_t(preds[k] if k in preds else set(), v))
#			for k, v in s_adjl.items() ] )
	g = { k : adjs_t(preds[k] if k in preds else set(), v)
			for k, v in s_adjl.items() }

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

#TODO	__check_directions(conns)
def __make_dag_alt(model, meta) :

	conns0 = { k : v for k, v in model.connections.items() if v }
	blocks, conns1, delays = __expand_delays(model.blocks, conns0)

	conns_rev = reverse_dict_of_lists(conns1, lambda values: list(set(values)))

	graph = { b : adjs_t(
			[ (t, conns_rev[(b, t)] if (b, t) in conns_rev else []) for t in __in_terms(b.terms) ],
			[ (t, conns1[(b, t)] if (b, t) in conns1 else []) for t in __out_terms(b.terms) ])
		for b in blocks }

	__expand_joints_new(graph)

	return graph, delays

# ------------------------------------------------------------------------------------------------------------

def __dft_alt_roots_sorter(leafs) :
	return sorted(leafs)
#	return leafs

def __dft_alt_p_sorter(preds) :
	for t, neighbours in preds :
		for b, mt in neighbours :
			yield t, b, mt

#def __dft_alt_is_root(n, neighbours) :
#	return 


def dft_alt_succs_count(s):
	return sum([ len(succ_blocks) for t, succ_blocks in s ])

# block is root if have no successors (no outputs, or all outputs are unconnected)
def __dft_alt_roots_selector(g, sinks_to_sources, roots_sorter) :
	p_or_s = 1 if sinks_to_sources else 0
#	s = roots_sorter([ v for v, neighbourhood in g.items()
#		if all([ len(follows) == 0 for t, follows in neighbourhood[p_or_s] ]) ])
	s = roots_sorter([ v for v, nbrhd in g.items() if dft_alt_succs_count(nbrhd[p_or_s]) == 0 ])
	return s

# ------------------------------------------------------------------------------------------------------------

def __dft_alt_dive(g, n, pre_visit, pre_dive, post_dive, post_visit, visited, visited_per_tree) :
	if not n in visited :
		visited.append(n)
		visited_per_tree[n] = True
		pre_visit(n, visited)
		for nt, m, mt in __dft_alt_p_sorter(g[n].p) : #g[n].p :
			pre_dive(n, nt, m, mt, visited)
			__dft_alt_dive(g, m, pre_visit, pre_dive, post_dive, post_visit, visited, visited_per_tree)
			assert(n in visited)
			assert(m in visited)
			post_dive(n, nt, m, mt, visited)
		post_visit(n, visited)

def __dft_alt_recursive(g, pre_visit, pre_dive, post_dive, post_visit, pre_tree, post_tree,
		roots_sorter=__dft_alt_roots_sorter, sinks_to_sources=True) :
#	s = roots_sorter([ v for v, (p, s) in g.items() if not ( s if sinks_to_sources else p ) ])
	s = __dft_alt_roots_selector(g, sinks_to_sources, roots_sorter)
	visited = [] #XXX what about dictionary? should be faster
	for v in s :
		pre_tree(v, visited)
		visited_per_tree = {}
		__dft_alt_dive(g, v, pre_visit, pre_dive, post_dive, post_visit, visited, visited_per_tree)
		post_tree(v, visited)

# ------------------------------------------------------------------------------------------------------------

def __dft_alt_nr_tree(g, root, pre_visit, pre_dive, post_dive, post_visit, visited, visited_per_tree) :
	stack = [ (root, None, __dft_alt_p_sorter(g[root].p)) ]
	pre_visit(root, visited)
	while stack :
		n, prev, it = stack[-1]
		if prev != None :
			nt, m, mt = prev
			assert(n in visited)
			assert(m in visited)
			post_dive(n, nt, m, mt, visited)
		try :
			nt, m, mt = it.next()
			stack[-1] = n, (nt, m, mt), it
			pre_dive(n, nt, m, mt, visited)
			if not m in visited :
				visited[m] = True
				pre_visit(m, visited)
				stack.append((m, None, __dft_alt_p_sorter(g[m].p)))
		except StopIteration :
			stack.pop(-1)
			post_visit(n, visited)

def __dft_alt_nonrecursive(g, pre_visit, pre_dive, post_dive, post_visit, pre_tree, post_tree,
		roots_sorter=__dft_alt_roots_sorter, sinks_to_sources=True) :
#	s = roots_sorter([ v for v, (p, s) in g.items() if not ( s if sinks_to_sources else p ) ])
	s = __dft_alt_roots_selector(g, sinks_to_sources, roots_sorter)
	visited = {}
	for v in s :
		pre_tree(v, visited)
		assert(not v in visited)
		visited[v] = True
		visited_per_tree = {}
		__dft_alt_nr_tree(g, v, pre_visit, pre_dive, post_dive, post_visit, visited, visited_per_tree)
		post_tree(v, visited)

# ------------------------------------------------------------------------------------------------------------

dft_alt = __dft_alt_nonrecursive
#dft_alt = __dft_alt_recursive

# ------------------------------------------------------------------------------------------------------------

def printg(g) :
	for b, (p, s) in g.items() :
		for t, x in s :
			print(str(b)+str(t))
			for nb, nt in x :
				print("\t -> %s%s"%(str(nb),str(nt)))

def implement_dfs(model, meta, codegen) :
#	from fcodegen import codegen
#	g, conns, delays = __make_dag(model, meta)
##	pprint(conns)
	graph, delays = __make_dag_alt(model, meta)
#	pprint(graph)

#	gsorted = [ __tsort(__graph_part(g, comp)) for comp in __components(g) ]

#TODO be aware of components
	code = codegen(graph, delays, {})

#	printg(graph)
	print(code)
	sys.exit(0)

#	gsorted = [ __tsort(__graph_part(g, comp)) for comp in __components(g) ]
#	print codegen(g, conns, delays, list(chain(*gsorted)))
#	return impl_t(None, None, None)

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
#TODO use meta to set task name (that is method name in generated code)
#TODO make states (delays) global
#TODO ...which requires initializer method
	cgens = {
		"c" : ccodegen.codegen_alt,
		"f" : fcodegen.codegen_alt,
	}
	out = implement_dfs(model, None, cgens[cgen])
	#print "out:", out
	exit(0)

# ------------------------------------------------------------------------------------------------------------


