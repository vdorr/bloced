
from dfs import *
from core import *
from collections import namedtuple
from functools import partial
from itertools import groupby, chain, count
from pprint import pprint
import sys

# ------------------------------------------------------------------------------------------------------------

#	model :
#	( from_block, from_term ) : [ ( to_block0, to_term0, ), ... ]

#TODO TODO TODO revisit
# convention: get_terms - last term in list is on top of stack
# assumption : every block is evaluated exactly once per iteration
#	- except constants
#	- evaluation of stateless components can (should) be optimized

# ------------------------------------------------------------------------------------------------------------

adjs_t = namedtuple("a", [ "p", "s", ])

# ------------------------------------------------------------------------------------------------------------

def groupby_to_dict(it, key_selector, value_selector, value_grouper) :
	return { key : value_grouper([ value_selector(val) for val in values ])
			for key, values in groupby(sorted(it, key=key_selector), key_selector) }

# ------------------------------------------------------------------------------------------------------------

def reverse_dict_of_lists(d, key_grouper) :
	l = list(chain(*[ [ (v, k) for v in values ] for k, values in d.items() ]))
	return groupby_to_dict(l, lambda i: i[0], lambda i: i[1], key_grouper)

# ------------------------------------------------------------------------------------------------------------

def dict_map(d, k_map, v_map, item_filter=lambda k,v: True) :
	return { k_map(*i): v_map(*i) for i in d.items() if item_filter(*i) }

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
		for t, nr, preds in p :
			if not t in b.prototype.terms :
				return (False, 0)
			if t.direction != INPUT_TERM :
				return (False, 1)
			if len(preds) != 1 :
				return (False, 2, (b, t, preds))
			for b_pred, t_pred, n_pred in preds :
				if not b_pred in g :
					return (False, 3)
				if t_pred.direction != OUTPUT_TERM :
					return (False, 4)
				if not t_pred in b_pred.prototype.terms :
					return (False, 5)
		for t, nr, succs in s :
			if not t in b.prototype.terms :
				return (False, 6)
			if t.direction != OUTPUT_TERM :
				return (False, 7)
			for b_succ, t_succ, n_succ in succs :
				if not b_succ in g :
					return (False, 8)
				if t_succ.direction != INPUT_TERM :
					return (False, 9)
				if not t_succ in b_succ.prototype.terms :
					return (False, 10)
	return (True, )

#TODO TODO TODO

# ------------------------------------------------------------------------------------------------------------

#def __neighbourhood_remove(neighbourhood, bt, block, term, term_nr) :
#	(neighbours, ) = [ succs for t, nr, succs in neighbours if t == bt]
##	if (block, term) in neighbours :
#	neighbours.remove((block, term, term_nr))

def __neighbourhood_add(neighbourhood, bt, block, term, term_nr) :
	(neighbours, ) = [ succs for t, succs in neighbours if t == bt]
	assert(not (block, term) in neighbours) # raise should be better
	neighbours.append((block, term))
	assert(len(neighbours)==1 if bt.direction == INPUT_TERM else True)

def __neighbourhood_safe_replace(neighbourhood, term, term_nr, old_pair, new_pair) :
#	print "__neighbourhood_safe_replace:", neighbourhood, term, term_nr
	(neighbours, ) = [ succs for t, nr, succs in neighbourhood if t == term and nr == term_nr ]
	if old_pair != None and old_pair in neighbours :
		neighbours.remove(old_pair)
	if new_pair != None and not new_pair in neighbours :
		neighbours.append(new_pair)

# ------------------------------------------------------------------------------------------------------------

# to implement __expand_joints_new and macro expansion

#XXX because of symmetry, there should be only single map
def __replace_block_with_subgraph(g, n, subgraph, map_in, map_out) :
	"""
	replace single block from g with subgraph, subgraph may be empty dict and function might be used
	to map block terminal to other blocks in g
	map_in = { (n_in_term, n_in_term_nr) : [ (subgraph_block, subgraph_term, subgraph_term_nr), ... ], ... }
	map_out = { (n_out_term, n_out_term_nr) : (subgraph_block, subgraph_term, subgraph_term_nr), ... }
	"""
#	print "map_in=", map_in
#	print "map_out=", map_out

	p, s = g.pop(n)
	g.update(subgraph)

#	print "__replace_block_with_subgraph(1)"
#	pprint(p)
#	print "__replace_block_with_subgraph(2)"

	npreds = { (t, n) : values for t, n, values in p }
	nsuccs = { (t, n) : values for t, n, values in s }

	for (in_t, in_t_nr), succs in map_in.items() :
		assert(in_t.direction == INPUT_TERM)
		((b_pred, t_pred, t_pred_nr),) = npreds[in_t, in_t_nr]
		for b, t, nr in succs :
			assert(t.direction == INPUT_TERM)
			assert(t_pred.direction == OUTPUT_TERM)
#			print b_pred, t_pred, "->", b, t
			#XXX something should be move outside this loop
#			__neighbourhood_safe_replace(neighbourhood, bt, old_pair, new_pair)
#			print "666:", g[b_pred].s, t_pred, t_pred_nr, t_pred==g[b_pred].s[0][0]
			__neighbourhood_safe_replace(g[b_pred].s, t_pred, t_pred_nr, (n, in_t, in_t_nr), (b, t, nr))
			__neighbourhood_safe_replace(g[b].p, t, nr, None, (b_pred, t_pred, t_pred_nr))

#	print "__replace_block_with_subgraph(3):", map_out.items()[0]
	for (out_t, out_t_nr), (b, t, nr) in map_out.items() :
		assert(out_t.direction == OUTPUT_TERM)
		assert(t.direction == OUTPUT_TERM)
		succs = nsuccs[(out_t, out_t_nr)]
		for b_succ, t_succ, t_succ_nr in succs :
#			print b, t, "->", b_succ, t_succ
			assert(t_succ.direction == INPUT_TERM)
			__neighbourhood_safe_replace(g[b_succ].p, t_succ, t_succ_nr, (n, out_t, out_t_nr), (b, t, nr))
			__neighbourhood_safe_replace(g[b].s, t, nr, None, (b_succ, t_succ, t_succ_nr))

	return None

# ------------------------------------------------------------------------------------------------------------

def __cut_joint_alt(g, j) :
#	print "__cut_joint_alt:", g[j].p
#	(((it, it_nr, ((pb, pt, pt_nr),)),), succs) = g[j]
	((it, it_nr, ((pb, pt, pt_nr),)),), succs = g[j]
	map_in = { (it, it_nr) : [ (b, t, nr) for (ot, ot_nr, ((b, t, nr),)) in succs ] } # works only for joints!
	map_out = { (out_term, out_term_nr) : (pb, pt, pt_nr) for out_term, out_term_nr, _ in succs }
	__replace_block_with_subgraph(g, j, {}, map_in, map_out)

#XXX is there a way how to do it functionally?
def __expand_joints_new(g) :
	for j in [ b for b in g if isinstance(b.prototype, JointProto) ] :
		__cut_joint_alt(g, j)

# ------------------------------------------------------------------------------------------------------------

def __join_tap(g, tap_ends, tap) :
	p, s = g[tap]
	tap_ends_lst = tap_ends.pop(tap.value)
	((_, _, ((pb, pt, pt_nr),)),) = p
	succs = []
	for tap_end in tap_ends_lst :
		tap_end_preds, tap_end_succs = g[tap_end]
		succs += tap_end_succs
		map_out = { (out_term, out_term_nr) : (pb, pt, pt_nr)
			for out_term, out_term_nr, _ in tap_end_succs }
		__replace_block_with_subgraph(g, tap_end, {}, {}, map_out)
		assert(not tap_end in g)
	map_in = { (tap.terms[0], 0) : [ (b, t, nr) for (ot, ot_nr, ((b, t, nr),)) in succs ] }
	__replace_block_with_subgraph(g, tap, {}, map_in, {})

def __join_taps(g) :
	tap_list = [ b for b, (p, s) in g.items() if isinstance(b.prototype, TapProto) ]
	taps = { b.value : b for b in tap_list }
	assert(len(tap_list)==len(taps))
	tap_ends_list = { b for b in g.keys() if isinstance(b.prototype, TapEndProto) }
	tap_ends = groupby_to_dict(tap_ends_list, lambda b: b.value, lambda b: b, lambda x: list(x))
	for tap_name, tap in taps.items() :
		__join_tap(g, tap_ends, tap)
	assert(len(tap_ends)==0)

# ------------------------------------------------------------------------------------------------------------

macro_t = namedtuple("macro_t", ("snippet", "mappings"))

def __instantiate_macro(g, library, mac) :
	assert(mac.value != None)
	snippet, mappings = library[mac.value]
	for b, (p, s) in snippet :
		pass
	return {}

def __expand_macro(g, library, mac) :
	assert(mac.value != None)
	mac_name = str(mac.value)
	mg = library[mac_name]

	subgraph, mapping = __instantiate_macro(g, library, mac)

#	((it, it_nr, ((pb, pt, pt_nr),)),), succs = g[mac]
	map_in = { (it, it_nr) : [ (b, t, nr) for (ot, ot_nr, ((b, t, nr),)) in succs ]
		for it, it_nr in get_terms_flattened(mac) }
	map_out = { (out_term, out_term_nr) : (pb, pt, pt_nr) for out_term, out_term_nr, _ in succs }

	__replace_block_with_subgraph(g, mac, subgraph, map_in, map_out)

def __expand_macroes(g, library) :
	for mac in [ b for b in g if isinstance(b.prototype, MacroProto) ] :
		__expand_macro(g, library, mac)

# ------------------------------------------------------------------------------------------------------------

def t_unpack(term) :
	return term if isinstance(term, tuple) else (term, 0) # XXX XXX use 0 instead of None?

def __expand_delays(blocks, conns) :

	delays = { b for b in blocks if isinstance(b.prototype, DelayProto) }

#	expddel_t = namedtuple("expddel_t", ["i", "o"])
	def expddel(d, nr) :
		i = BlockModel(DelayInProto(), None)
		o = BlockModel(DelayOutProto(), None)
		i.nr = o.nr = nr
		i.delay = o.delay = d
		return (d, (i, o)) # TODO return expddel_t((i, i.terms[0]), (o, o.terms[0]))

	expd = dict([ expddel(delay, nr) for delay, nr in zip(delays, count()) ])
#	print expd

#def dict_map(d, k_map, v_map, item_filter=lambda k,v: True) :
#	return { k_map(*i): v_map(*i) for i in d.items() if item_filter(*i) }

	def mkvert(src, io) :
		b, t = src
		block, term = ( ( expd[b][io], expd[b][io].terms[0] )
			if isinstance(b.prototype, DelayProto)
			else (b, t) )
		return (block, ) + t_unpack(term)

#	def mkdest(dst) :
#		b, t = dst
#		block, term = ( (expd[b].i, expd[b].i.terms[0])
#			if isinstance(b.prototype, DelayProto)
#			else (b, t) )
#		return (block, ) + t_unpack(term)

	conns2 = { mkvert(s, 1) : [ mkvert(d, 0) for d in dests ] for s, dests in conns.items() }

#	conns2 = dict_map(conns,
#		lambda k, v: (
#			(expd[k[0]].o, t_unpack(expd[k[0]].o.terms[0]))
#			if isinstance(k[0].prototype, DelayProto)
#			else (k[0], t_unpack(k[1]))
#		),
#		lambda k, values: [
#			(expd[b].i, t_unpack(expd[b].i.terms[0]))
#			if isinstance(b.prototype, DelayProto)
#			else (b, t_unpack(t))
#				for b, t in values
#		])

	return list((set(blocks)-delays).union(chain(*expd.values()))), conns2, expd

# ------------------------------------------------------------------------------------------------------------

def get_terms_flattened(block) :
	for t in block.terms :
		if t.variadic :
			for nr, index in sorted(block.get_indexed_terms(t), key=lambda x: x[1])[:-1] :
				yield t, nr
		else :
			yield t, 0

def __in_terms(block) :
#	print "__in_terms:", block.__class__
#TODO TODO TODO proper sorting!!!!!
	return [ (t, n) for t, n in get_terms_flattened(block) if t.direction == INPUT_TERM  ]
#	return [ (t, n if n != None else 0) for t, n in block.get_terms_flat() if t.direction == INPUT_TERM  ]
#	return [ t for t in block.terms if t.direction == INPUT_TERM  ]

def __out_terms(block) :
#TODO TODO TODO proper sorting!!!!!
	return [ (t, n) for t, n in get_terms_flattened(block) if t.direction == OUTPUT_TERM  ]
#	return [ (t, n if n != None else 0) for t, n in block.get_terms_flat() if t.direction == OUTPUT_TERM  ]
#	return [ t for t in block.terms if t.direction == OUTPUT_TERM  ]

#def __adj_edges(b, conns, neighbours) :
#	inputs
#	outputs

#def __adj_in_edges(b, conns, neighbours) :
#	preds = reverse_dict_of_lists(s_adjl, lambda values: set(values))
#	print b, "inputs:", __in_terms(b.prototype.terms)

#def __adj_out_edges(b, conns, neighbours) :
##	print b, neighbours
#	print b, "outputs:", __out_terms(b.prototype.terms)
##	return { st : dst for (sb, st), dst in conns.items() if src[0] in neighbours }

def __merge_g_and_conns(g, conns) :
	return { b : adjs_t(__adj_in_edges(b, conns, p), __adj_out_edges(b, conns, s)) for b, (p, s) in g.items() }

# ------------------------------------------------------------------------------------------------------------

#TODO	__check_directions(conns)
def make_dag(model, meta) :
	conns0 = { k : v for k, v in model.connections.items() if v }
	blocks, conns1, delays = __expand_delays(model.blocks, conns0)

#	pprint(model.connections)
#	exit(666)

	conns_rev = reverse_dict_of_lists(conns1, lambda values: list(set(values)))
	graph = { b : adjs_t(
			[ (t, n, conns_rev[(b, t, n)] if (b, t, n) in conns_rev else []) for t, n in __in_terms(b) ],
			[ (t, n, conns1[(b, t, n)] if (b, t, n) in conns1 else []) for t, n in __out_terms(b) ])
		for b in blocks }
#	pprint(
#	{ b : (#adjs_t(
#			__in_terms(b),#[ (t, conns_rev[(b, t, n)] if (b, t, n) in conns_rev else []) for t, n in __in_terms(b) ],
#			__out_terms(b),#[ (t, conns1[(b, t, n)] if (b, t, n) in conns1 else []) for t, n in __out_terms(b) ])
#		) for b in blocks }
#)
	is_sane = __dag_sanity_check(graph, stop_on_first=False)
	if not is_sane :
		raise Exception("make_dag: produced graph is insane")

	__expand_joints_new(graph)
	__join_taps(graph)

	return graph, delays

# ------------------------------------------------------------------------------------------------------------

def __dft_alt_roots_sorter(g, roots) :
	comps = {}
	for comp, number in zip(graph_components(g), count()) :
		comps.update({ n : number for n in comp})
	return sorted(roots, key=lambda n: comps[n])
#	return leafs

def __dft_alt_term_sorter(preds) :
	for t, t_nr, neighbours in preds :
		for b, mt, nr in neighbours :
			yield t, t_nr, b, mt, nr

#def __dft_alt_is_root(n, neighbours) :
#	return 


def dft_alt_succs_count(s):
	return sum([ len(succ_blocks) for t, nr, succ_blocks in s ])

# block is root if have no successors (no outputs, or all outputs are unconnected)
def __dft_alt_roots_selector(g, sinks_to_sources, roots_sorter) :
	p_or_s = 1 if sinks_to_sources else 0
#	s = roots_sorter([ v for v, neighbourhood in g.items()
#		if all([ len(follows) == 0 for t, follows in neighbourhood[p_or_s] ]) ])
	s = roots_sorter(g, [ v for v, nbrhd in g.items() if dft_alt_succs_count(nbrhd[p_or_s]) == 0 ])
	return s

# ------------------------------------------------------------------------------------------------------------

#def __dft_alt_dive(g, n, pre_visit, pre_dive, post_dive, post_visit, visited, visited_per_tree) :
#	if not n in visited :
#		visited.append(n)
#		visited_per_tree[n] = True
#		pre_visit(n, visited)
#		for nt, m, mt in __dft_alt_p_sorter(g[n].p) : #g[n].p :
#			pre_dive(n, nt, m, mt, visited)
#			__dft_alt_dive(g, m, pre_visit, pre_dive, post_dive, post_visit, visited, visited_per_tree)
#			assert(n in visited)
#			assert(m in visited)
#			post_dive(n, nt, m, mt, visited)
#		post_visit(n, visited)

#def __dft_alt_recursive(g, pre_visit, pre_dive, post_dive, post_visit, pre_tree, post_tree,
#		roots_sorter=__dft_alt_roots_sorter, sinks_to_sources=True) :
##	s = roots_sorter([ v for v, (p, s) in g.items() if not ( s if sinks_to_sources else p ) ])
#	s = __dft_alt_roots_selector(g, sinks_to_sources, roots_sorter)
#	visited = [] #XXX what about dictionary? should be faster
#	for v in s :
#		pre_tree(v, visited)
#		visited_per_tree = {}
#		__dft_alt_dive(g, v, pre_visit, pre_dive, post_dive, post_visit, visited, visited_per_tree)
#		post_tree(v, visited)

# ------------------------------------------------------------------------------------------------------------

def __where_to_go(neighbourhood, sinks_to_sources, undirected) :
	if undirected :
		return neighbourhood.p + neighbourhood.s
	elif sinks_to_sources :
		return neighbourhood.p
	else :
		return neighbourhood.s

def __dft_alt_nr_tree(g, root, pre_visit, pre_dive, post_dive, post_visit, visited, sinks_to_sources, undir) :
	terms = list(__dft_alt_term_sorter(__where_to_go(g[root], sinks_to_sources, undir)))
	pre_visit(root, visited, terms)
	stack = [ (root, None, terms.__iter__()) ]
	while stack :
		n, prev, it = stack[-1]
		if prev != None :
			nt, nt_nr, m, mt, mt_nr = prev
			assert(n in visited)
			assert(m in visited)
			post_dive(n, nt, nt_nr, m, mt, mt_nr, visited)
		try :
			nt, nt_nr, m, mt, mt_nr = it.next()
			stack[-1] = n, (nt, nt_nr, m, mt, mt_nr), it
			pre_dive(n, nt, nt_nr, m, mt, mt_nr, visited)
			if not m in visited :
				visited[m] = True
				terms = list(__dft_alt_term_sorter(__where_to_go(g[m], sinks_to_sources, undir)))
				pre_visit(m, visited, terms)
				stack.append((m, None, terms.__iter__()))
		except StopIteration :
			stack.pop(-1)
			post_visit(n, visited)

def dft(g, v,
		pre_visit = lambda *a, **b: None,
		pre_dive = lambda *a, **b: None,
		post_dive = lambda *a, **b: None,
		post_visit = lambda *a, **b: None,
		sinks_to_sources=True,
		undirected=False,
		visited={}) :
	visited[v] = True
	__dft_alt_nr_tree(g, v, pre_visit, pre_dive, post_dive, post_visit, visited,
		sinks_to_sources, undirected)

# ------------------------------------------------------------------------------------------------------------

def dft_alt(g,
		pre_visit = lambda *a, **b: None,
		pre_dive = lambda *a, **b: None,
		post_dive = lambda *a, **b: None,
		post_visit = lambda *a, **b: None,
		pre_tree = lambda *a, **b: None,
		post_tree = lambda *a, **b: None,
		roots_sorter=__dft_alt_roots_sorter,
		sinks_to_sources=True) :
#	s = roots_sorter([ v for v, (p, s) in g.items() if not ( s if sinks_to_sources else p ) ])
	s = __dft_alt_roots_selector(g, sinks_to_sources, roots_sorter)
	visited = {}
	for v in s :
		pre_tree(v, visited)
		assert(not v in visited)
		visited[v] = True
#		visited_per_tree = {}
#		__dft_alt_nr_tree(g, v, pre_visit, pre_dive, post_dive, post_visit, visited, visited_per_tree,
#			sinks_to_sources, False)
		dft(g, v, pre_visit, pre_dive, post_dive, post_visit, sinks_to_sources, False, visited)
#		dft(g, v,
#			pre_visit = pre_visit,
#			pre_dive = pre_dive,
#			post_dive = post_dive,
#			post_visit = post_visit,
#			sinks_to_sources=sinks_to_sources,
#			undirected=False,
#			visited=visited) 
		post_tree(v, visited)

# ------------------------------------------------------------------------------------------------------------

def graph_components(g) :
	comps = []
	visited={}
	for v in g.keys() :
		comp={}
		if not v in visited :
			dft(g, v, undirected=True, visited=comp)
			visited.update(comp)
			comps.append(comp.keys())
	return comps

# ------------------------------------------------------------------------------------------------------------

def __su_post_visit(g, numbering, n, visited) :
#TODO add documentation
#TODO take into account temp variables?
	"""
	commutativity comes in two flavours, it may be commutative block,
	or numbered instances of variadic terminal
	"""
	p, s = g[n] # XXX s might be used to analyze spill space usage
	src_blocks1 = [ (t, nr, src_b, i) for ((t, nr, ((src_b, src_t, src_t_nt),)), i) in zip(p, count()) ]
	if n.prototype.commutative :
		src_grouped = ( ( None, sorted(src_blocks1, key=lambda (t, nr, src_b, i) : -numbering[src_b][0]) ), )
	else :
		src_grouped = [ (t, list(rest)) for t, rest in groupby(src_blocks1, lambda (term, _0, _1, _2): term) ]
	index = 0
	evaluated_blocks = []
	usages = []
	indices = []
	for group_term, src_blocks in src_grouped :
		if not n.prototype.commutative and group_term.commutative:
			src_blocks = sorted(src_blocks, key=lambda (t, nr, src_b, i) : -numbering[src_b][0])
		for term, nr, src_b, i in src_blocks :
			if not src_b in evaluated_blocks :
				usages.append(numbering[src_b][0] + index)
				index += 1
			else :
				index += 1
				usages.append(index)
			evaluated_blocks.append(src_b)
			indices.append(i)
	slots = max( usages + [ len(s) ] )
	numbering[n] = ( slots, indices )

def sethi_ullman(g) :
#TODO testing, is it (easily) possible to algorithmically create graph with given numbering?
	numbering = {}
	dft_alt(g, post_visit = partial(__su_post_visit, g, numbering))
	return numbering

# ------------------------------------------------------------------------------------------------------------

#TODO testing
#TODO it may be better to use dictionary

# TODO may have limit parameter and generate spill code
def temp_init() :
	return []

# ------------------------------------------------------------------------------------------------------------

def get_tmp_slot(tmp) :
	if "empty" in tmp :
		slot = tmp.index("empty")
	else :
		slot = len(tmp)
		tmp.append("empty")
	return slot

# ------------------------------------------------------------------------------------------------------------

def add_tmp_ref(tmp, refs) :
	assert(len(refs)>0)
	slot = get_tmp_slot(tmp)
	tmp[slot] = list(refs)
	return slot

# ------------------------------------------------------------------------------------------------------------

def pop_tmp_ref(tmp, b, t, t_nr) :
#	print "tmp=", tmp, "searching:", b, t
	for slot, nr in zip(tmp, count()) :
		if slot != "empty" and (b, t, t_nr) in slot :
			slot.remove((b, t, t_nr))
			if len(slot) == 0 :
				tmp[nr] = "empty"
#			else :
#				print "pop_tmp_ref:", tmp[nr]
			return nr
	return None

# ------------------------------------------------------------------------------------------------------------

def tmp_used_slots(tmp) :
	assert( sum([ 1 for slot in tmp if slot != "empty"])== reduce(lambda cnt, slot: cnt + (0 if slot == "empty" else 1), tmp, 0))
	return sum([ 1 for slot in tmp if slot != "empty" ])

# ------------------------------------------------------------------------------------------------------------

def printg(g) :
	for b, (p, s) in g.items() :
		for t, x in s :
			print(str(b)+str(t))
			for nb, nt in x :
				print("\t -> %s%s"%(str(nb),str(nt)))

# ------------------------------------------------------------------------------------------------------------

def implement_dfs(model, meta, codegen, out_fobj) :
	graph, delays = make_dag(model, meta)
	code = codegen(graph, delays, {})
	out_fobj.write(code)#XXX pass out_fobj to codegen?

# ------------------------------------------------------------------------------------------------------------

def __mc_term_info(model, tb) :
	(x, y), _ = tb.get_term_and_lbl_pos(tb.terms[0], 0, 0, 0)
	return (tb, (tb.left+x, tb.top+y))

#def __mc_assign_side(tb, k, w, u, x, y) :
#	sides = {
#		(True, True) : N,
#		(False, False) : S,
#		(True, False) : W,
#		(False, True) : E
#	}
#	print tb, x, y,  y>(k * x), y>((-k * (x-w))+u)
#	return sides[y>(k * x), y>((-k * (x-w))+u)]

def __mc_assign_side(tb, center_x, center_y, x, y) :
	sides = {
		(True, True) : S,
		(True, False) : N,
		(False, True) : E,
		(False, False) : W
	}
	side = tb.terms[0].get_side(tb)
	vertical = side in (N, S)
#	print tb, x, y,  y>(k * x), y>((-k * (x-w))+u)
	return sides[vertical, y > center_y if vertical else x > center_x ]

def try_mkmac(model) :
#	inputs = [ b for b in model.blocks if isinstance(b.prototype, InputProto) ]
#	outputs = [ b for b in model.blocks if isinstance(b.prototype, OutputProto) ]

	terms = [ __mc_term_info(model, b)
		for b in model.blocks if b.prototype.__class__ in (InputProto, OutputProto) ]
	print "try_mkmac:", terms

	if terms :
		(l, t, r, b) = reduce(lambda (l0, t0, r0, b0), (l1, t1, r1, b1): (
				l1 if l1 < l0 else l0,
				t1 if t1 < t0 else t0,
				r1 if r1 > r0 else r0,
				b1 if b1 > b0 else b0),
			[ (x, y, x, y) for _, (x, y) in terms ])
	else :
		(l, t, r, b) = (0, 0, 48, 48)
#	(l, t, r, b) = (l-1, t-1, r+1, b+1)

#	k = float(b) / float(r)# (l,t) (r,b)
##	k = float(b-t) / float(r-l)# (l,t) (r,b)
##	kb = float(t-b) / float(r-l) # (l,b) (r,t)
	print "try_mkmac: l, t, r, b, w,h=", l, t, r, b, r-l, b-t

	term_sides = [ (tb, __mc_assign_side(tb, l+((r-l)/2), t+((b-t)/2), x, y), (x, y)) for tb, (x, y) in terms]
#	xxx = [ (tb, __mc_assign_side(tb, k, (r-l)/2, (b-t), x, y)) for tb, (x, y) in terms]
	print "try_mkmac: sides=", term_sides

#	term_WE = [ (tb, side) for tb, side in term_sides if side in (W, E) ]
#	term_NS = [ (tb, side) for tb, side in term_sides if side in (N, S) ]

#	term_W = [ (tb, side, x, y) for tb, side, (x, y) in term_sides if side == W ]
#	term_E = [ (tb, side, x, y) for tb, side, (x, y) in term_sides if side == E ]
#	term_S = [ (tb, side, x, y) for tb, side, (x, y) in term_sides if side == S ]
#	term_N = [ (tb, side, x, y) for tb, side, (x, y) in term_sides if side == N ]

	term_W = [ (tb, side, y) for tb, side, (x, y) in term_sides if side == W ]
	term_W = sorted(term_W, key=lambda (tb, side, y): y)
	step = 1.0 / (len(term_W) + 1)
	term_positions = [ (tb, side, (i + 1) * step) for (tb, side, p), i in zip(term_W, count()) ]
	print "step=", step, "term_positions=", term_positions

	term_E = [ (tb, side, y) for tb, side, (x, y) in term_sides if side == E ]
	term_S = [ (tb, side, x) for tb, side, (x, y) in term_sides if side == S ]
	term_N = [ (tb, side, x) for tb, side, (x, y) in term_sides if side == N ]


#	graph, delays = make_dag(model, {})
#	pprint(graph)

# ------------------------------------------------------------------------------------------------------------

if __name__ == "__main__" :
#	import argparse
#	parser = argparse.ArgumentParser(description="bloced")
#	parser.add_argument("file", metavar="fname", type=str, nargs=1,
#                   help="input file")
#	args = parser.parse_args()
#	fname = args.file[0]
	from serializer import unpickle_dfs_model
	action = sys.argv[1]
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
#TODO use meta to set task name (that is, method name in generated code)
#TODO make states (delays) global
#TODO ...which requires initializer method
	cgens = {
		"c" : ccodegen.codegen_alt,
		"f" : fcodegen.codegen_alt,
	}
	if action in cgens :
		class DummyFile(object):
			def write(self, s) :
				print(s)
		out_fobj = DummyFile()
		implement_dfs(model, None, cgens[cgens], out_fobj)
		exit(0)
	elif action == "mkmac" :
		try_mkmac(model)
		exit(0)
	exit(666)

# ------------------------------------------------------------------------------------------------------------


