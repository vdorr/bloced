#! /usr/bin/python

import dfs
import core
from collections import namedtuple
from functools import partial
from itertools import groupby, chain, count, islice
from pprint import pprint
import sys
from hashlib import md5
import os
from utils import here
if sys.version_info.major == 3 :
	from functools import reduce

# ------------------------------------------------------------------------------------------------------------

adjs_t = namedtuple("a", [ "p", "s", ])

# ------------------------------------------------------------------------------------------------------------

def groupby_to_dict(it, key_selector, value_selector, value_grouper) :
	return { key : value_grouper([ value_selector(val) for val in values ])
			for key, values in groupby(sorted(it, key=key_selector), key_selector) }


def reverse_dict_of_lists(d, key_grouper) :
	l = list(chain(*[ [ (v, k) for v in values ] for k, values in d.items() ]))
	return groupby_to_dict(l, lambda i: i[0], lambda i: i[1], key_grouper)


def dict_map(d, k_map, v_map, item_filter=lambda k, v: True) :
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
			if t.direction != core.INPUT_TERM :
				return (False, 1)
			if len(preds) != 1 :
				return (False, 2, (b, t, preds))
			for b_pred, t_pred, n_pred in preds :
				if not b_pred in g :
					return (False, 3)
				if t_pred.direction != core.OUTPUT_TERM :
					return (False, 4)
				if not t_pred in b_pred.prototype.terms :
					return (False, 5)
		for t, nr, succs in s :
			if not t in b.prototype.terms :
				return (False, 6)
			if t.direction != core.OUTPUT_TERM :
				return (False, 7)
			for b_succ, t_succ, n_succ in succs :
				if not b_succ in g :
					return (False, 8)
				if t_succ.direction != core.INPUT_TERM :
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


#def __neighbourhood_add(neighbourhood, bt, block, term, term_nr) :
#	(neighbours, ) = [ succs for t, succs in neighbours?!?!?!? if t == bt]
#	assert(not (block, term) in neighbours) # raise should be better
#	neighbours.append((block, term))
#	assert(len(neighbours)==1 if bt.direction == core.INPUT_TERM else True)


def __neighbourhood_safe_replace(neighbourhood, term, term_nr, old_tuple, new_tuple) :
	"""
	new/old_tuple = (block, block_term, block_term_number)
	"""
#	print "__neighbourhood_safe_replace:", neighbourhood, term, term_nr
	(neighbours, ) = [ succs for t, nr, succs in neighbourhood if t == term and nr == term_nr ]
	if old_tuple != None and old_tuple in neighbours :
		neighbours.remove(old_tuple)
	if new_tuple != None and not new_tuple in neighbours :
		neighbours.append(new_tuple)

# ------------------------------------------------------------------------------------------------------------

# to implement __expand_joints_new and macro expansion

def __replace_block_with_subgraph(g, n, subgraph, map_in, map_out) :
	"""
	replace single block from g with subgraph, subgraph may be empty dict and function might be used
	to map block terminal to other blocks in g
	map_in = { (n_in_term, n_in_term_nr) : [ (subgraph_block, subgraph_term, subgraph_term_nr), ... ], ... }
	map_out = { (n_out_term, n_out_term_nr) : (subgraph_block, subgraph_term, subgraph_term_nr), ... }
	"""
	return remove_block_and_patch(g, n, subgraph, map_in,
		{ k : (v,) for k, v in map_out.items() })


#def __check_mapping_sanity(mapping, dir_from, use_assert=True) :
#	def check(term) :
#		if use_assert :
#			assert(term.direction == dir_from)
#		else :
#			return term.direction == dir_from
#	for (in_t, in_t_nr), succs in mapping.items() :
#		check(in_t.direction)
#		for b, t, nr in succs :
#			check(t.direction)


#def neighbourhood_from_term_dir(ps, direction) :
#	"""
#	return (p, s) or (s, p) based on value of direction, that is list with terms of given direction first
#	"""
#	p, s = ps
#	if direction == core.INPUT_TERM :
#		return s, p
#	elif direction == core.OUTPUT_TERM :
#		return p, s
#	else :
#		raise Exception("unknown term direction")


#def __do_part_block_replace(g, n, adj, mapping, dir_from, dir_to) :
##TODO
#	pass


#XXX because of symmetry, there should be only single map
def remove_block_and_patch(g, n, subgraph, map_in, map_out) :
	"""
	replace single block from g with subgraph, subgraph may be empty dict and function might be used
	to map block terminal to other blocks in g
	map_in = { (n_in_term, n_in_term_nr) : [ (subgraph_block, subgraph_term, subgraph_term_nr), ... ], ... }
	map_out = { (n_out_term, n_out_term_nr) : [ (subgraph_block, subgraph_term, subgraph_term_nr), ... ], ... }
	"""

	p, s = g.pop(n)
	g.update(subgraph)

#TODO unify loops

#	__do_part_block_replace(g, n, s, map_out, core.OUTPUT_TERM, core.INPUT_TERM)
#	__do_part_block_replace(g, n, p, map_in, core.INPUT_TERM, core.OUTPUT_TERM)
#	return None

	for in_t, in_t_nr, values in p :
		assert(in_t.direction == core.INPUT_TERM)
		succs = map_in[in_t, in_t_nr] if (in_t, in_t_nr) in map_in else []
		for b_pred, t_pred, t_pred_nr in values :
			assert(t_pred.direction == core.OUTPUT_TERM)
			b_pred_succ = g[b_pred].s
			__neighbourhood_safe_replace(b_pred_succ, t_pred, t_pred_nr, (n, in_t, in_t_nr), None) #remove connection to n
			for b, t, nr in succs :
				assert(t.direction == core.INPUT_TERM)
				__neighbourhood_safe_replace(b_pred_succ, t_pred, t_pred_nr, (n, in_t, in_t_nr), (b, t, nr))
				__neighbourhood_safe_replace(g[b].p, t, nr, None, (b_pred, t_pred, t_pred_nr))

	for out_t, out_t_nr, values in s :
		assert(out_t.direction == core.OUTPUT_TERM)
		preds = map_out[out_t, out_t_nr] if (out_t, out_t_nr) in map_out else []
		for b_succ, t_succ, t_succ_nr in values :
			assert(t_succ.direction == core.INPUT_TERM)
			b_succ_pred = g[b_succ].p
			__neighbourhood_safe_replace(b_succ_pred, t_succ, t_succ_nr, (n, out_t, out_t_nr), None) #remove connection to n
			for b, t, nr in preds :
				assert(t.direction == core.OUTPUT_TERM)
				__neighbourhood_safe_replace(b_succ_pred, t_succ, t_succ_nr, (n, out_t, out_t_nr), (b, t, nr))
				__neighbourhood_safe_replace(g[b].s, t, nr, None, (b_succ, t_succ, t_succ_nr))


#	for (n_t, n_t_nr, values), mapping, dir_from, dir_to in ((s, map_out, core.OUTPUT_TERM, core.INPUT_TERM),) :
#		assert(n_t.direction == dir_from)
#		replacement = mapping[n_t, n_t_nr] if (n_t, n_t_nr) in mapping else []
#		for b_adj, t_adj, t_adj_nr in values :
#			assert(t_adj.direction == dir_to)
#			b_adj_pred, _ = neighbourhood_from_term_dir(g[b_adj], dir_from)
#			__neighbourhood_safe_replace(b_adj_pred, t_adj, t_adj_nr, (n, out_t, out_t_nr), None) #remove connection to n
#			for b, t, nr in replacement :
#				assert(t.direction == dir_from)
#				__neighbourhood_safe_replace(b_adj_pred, t_adj, t_adj_nr, (n, out_t, out_t_nr), (b, t, nr))
#				_, b_succs = neighbourhood_from_term_dir(g[b], dir_from)
#				__neighbourhood_safe_replace(b_succs, t, nr, None, (b_adj, t_adj, t_adj_nr))

	return None


def printg(g) :
	for b, (_, s) in g.items() :
		for t, x in s :
			print(str(b)+str(t))
			for nb, nt in x :
				print("\t -> %s%s"%(str(nb), str(nt)))


def dag_merge(l) :
	g, d = {}, {}
	for graph0, delays0 in l :
		g.update(graph0)
		d.update(delays0)
	return g, d


def chain_blocks(g, n, m) :
	"""
	creates artificial edge n -> m, so that order of evaluation is guaranteed to be n m
	motivated by need to express calls in main function, this is probably BAD THING
	"""
	n_out = core.VirtualOut("y")
	m_in = core.VirtualIn("x")
	g[n].s.insert(0, ((n_out, 0, [ (m, m_in, 0) ])))
	g[m].p.insert(0, ((m_in, 0, [ (n, n_out, 0) ])))


def replace_block(g, n, m) :
	p, s = g.pop(n)
	for t, t_nr, adj in p :
		new_term, = (tnew for tnew in m.terms if tnew.name == t.name)
		for b, bt, bt_nr in adj :
			__neighbourhood_safe_replace(g[b].s, bt, bt_nr, (n, t, t_nr), (m, new_term, t_nr))
	for t, t_nr, adj in s :
		new_term, = (tnew for tnew in m.terms if tnew.name == t.name)
		for b, bt, bt_nr in adj :
			__neighbourhood_safe_replace(g[b].p, bt, bt_nr, (n, t, t_nr), (m, new_term, t_nr))
	g[m] = adjs_t(
		[ ( [tnew for tnew in m.terms if tnew.name == t.name][0], t_nr, adj) for t, t_nr, adj in p ],
		[ ( [tnew for tnew in m.terms if tnew.name == t.name][0], t_nr, adj) for t, t_nr, adj in s ])


def remove_block(g, n) :
	"""
	remove block n from graph g
	"""
	map_in = { (t, t_nr) : tuple() for t, t_nr in in_terms(n) }
	map_out = { (t, t_nr) : tuple() for t, t_nr in out_terms(n) }
	remove_block_and_patch(g, n, {}, map_in, map_out)


def block_value_by_name(n, value_name) :
	return { name : value for (name, _), value in zip(n.prototype.values, n.value) }[value_name]


# ------------------------------------------------------------------------------------------------------------


def __cut_joint_alt(g, j) :
	((it, it_nr, ((pb, pt, pt_nr),)),), succs = g[j]
#	map_in = { (it, it_nr) : [ (b, t, nr) for (ot, ot_nr, ((b, t, nr),)) in succs ] } # works only for joints!
	map_in = { (it, it_nr) : [ v for _, _, vertices in succs for v in vertices ] } # works only for joints!
	map_out = { (out_term, out_term_nr) : (pb, pt, pt_nr) for out_term, out_term_nr, _ in succs }
	__replace_block_with_subgraph(g, j, {}, map_in, map_out)


#XXX is there a way how to do it functionally?
def __expand_joints_new(g) :
	for j in [ b for b in g if core.compare_proto_to_type(b.prototype, core.JointProto) ] :
		__cut_joint_alt(g, j)

# ------------------------------------------------------------------------------------------------------------


def __join_one_tap(g, tap_ends_lst, tap) :
	p, s = g[tap]
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


def get_taps(g) :
	"""
	return { tap_name : tap, ... }
	"""
	tap_list = [ b for b, (p, s) in g.items() if core.compare_proto_to_type(b.prototype, core.TapProto) ]
	taps = { b.value : b for b in tap_list }
	assert(len(tap_list)==len(taps))
	return taps


def get_tap_ends(g) :
	"""
	return { tap_name : [ tap_end1, ...], ... }
	"""
	tap_ends_list = { b for b in g.keys() if core.compare_proto_to_type(b.prototype, core.TapEndProto) }
	tap_ends = groupby_to_dict(tap_ends_list, lambda b: b.value, lambda b: b, lambda x: list(x))
	assert( len(tap_ends_list) == sum([len(v) for v in tap_ends.values()]) )
	return tap_ends


def join_taps(g) :
	taps = get_taps(g)
	tap_ends = get_tap_ends(g)
	additions = {}
	for tap_name, tap in taps.items() :
		tap_end = tap_ends.pop(tap.value) #TODO do not pop
		__join_one_tap(g, tap_end, tap)


# ------------------------------------------------------------------------------------------------------------

def t_unpack(term) :
	return term if isinstance(term, tuple) else (term, 0)


def __expddel(d, nr) :
	i = dfs.BlockModel(core.DelayInProto(), None)
#	print here(), d, nr
	if core.compare_proto_to_type(d.prototype, core.InitDelayProto) :
#		print here()
		o = dfs.BlockModel(core.InitDelayOutProto(), None)
	else :
		o = dfs.BlockModel(core.DelayOutProto(), None)
	i.nr = o.nr = nr
	i.delay = o.delay = d
	return d, (i, o)


def __mkvert(src, expd) :
	b, t0 = src
	t, _ = t_unpack(t0)

	if core.compare_proto_to_type(b.prototype, core.DelayProto, core.InitDelayProto) :
		block = expd[b][ 1 if t.name in ("y", "init") else 0 ]
		term, = get_terms_flattened(block, direction=t.direction)
#	if core.compare_proto_to_type(b.prototype, core.DelayProto) :
#		io = 1 if t.direction == core.OUTPUT_TERM else 0
#		block = expd[b][io]
#		term, = block.terms
#	elif core.compare_proto_to_type(b.prototype, core.InitDelayProto) :
#		io = 1 if t.name in ("y", "init") else 0
#		block = expd[b][io]
#		print here(), src, block, tuple(get_terms_flattened(block, direction=t.direction)), io
#		term, = get_terms_flattened(block, direction=t.direction)
	else :
		block, term = src

	result_t, result_t_nr = t_unpack(term)
	assert(t.direction==result_t.direction)
	return (block, result_t, result_t_nr)


def __expand_delays(blocks, conns, delay_numbering_start) :

	delays = frozenset(b for b in blocks
		if core.compare_proto_to_type(b.prototype, core.DelayProto, core.InitDelayProto))
#	delays = { b for b in blocks if core.compare_proto_to_type(b.prototype, core.DelayProto) }
#	print here(), delays

	expd = dict(__expddel(delay, delay_numbering_start + nr) for delay, nr in zip(delays, count()))
#	print here(), expd

#	def mkvert(src, io) :
#		b, t = src
#		block, term = ( ( expd[b][io], expd[b][io].terms[0] )
#			if core.compare_proto_to_type(b.prototype, core.DelayProto)
#			else (b, t) )

#		return (block, ) + t_unpack(term)

	conns2 = {}
	for s, dests in conns.items() :
		k = __mkvert(s, expd)
		v = [ __mkvert(d, expd) for d in dests ]
#		print here(), "s:", s, "dests:", dests, #"k:", k, "v:", v
		conns2[k] = v

#	sys.exit(0)

#	conns2 = { __mkvert(s, 1, expd) : [ __mkvert(d, 0, expd) for d in dests ] for s, dests in conns.items() }

	return list((set(blocks)-delays).union(chain(*expd.values()))), conns2, expd


#TODO TODO TODO proper sorting by prototype stack order
def get_terms_flattened(block, direction=None, fill_for_unconnected_var_terms=False) :
	for t in block.terms :
		if not direction is None and direction != t.direction :
			continue
		if t.variadic :
			for nr, index in sorted(block.get_indexed_terms(t), key=lambda x: x[1])[:-1] :
				yield t, nr
			else :
				if fill_for_unconnected_var_terms :
					yield t, None
		else :
			yield t, 0


def in_terms(block) :
#	return [ (t, n) for t, n in get_terms_flattened(block) if t.direction == core.INPUT_TERM  ]
	return tuple(get_terms_flattened(block, direction=core.INPUT_TERM))


def out_terms(block) :
#	return [ (t, n) for t, n in get_terms_flattened(block) if t.direction == core.OUTPUT_TERM  ]
	return tuple(get_terms_flattened(block, direction=core.OUTPUT_TERM))


# ------------------------------------------------------------------------------------------------------------

value_t = namedtuple("value_t", [ "value_type", "value"])#, "resource" 


def __parse_num_lit(value, base=10, known_types=None) :
	s = value.strip().lower()
	if (s[-1] == "f" and not s.startswith("0x")) or "." in s :
		return ("vm_float_t", float(s))
	else :
		if s[-1] == "l" :
			return ("vm_dword_t", int(s[:-1], base))
		else :
			v = int(s, base)
			val_type = "vm_word_t"
			if known_types :
				w_bytes = known_types["vm_word_t"].size_in_bytes
				over = v > (2 ** ((w_bytes * 8 ) - 1) - 1)
				val_type = "vm_dword_t" if over else "vm_word_t"
			return (val_type, v)


def parse_literal(s, known_types=None, variables={}) :
#TODO datetime values, physical units
	x = s.strip()
	num_sig = (x[1:].strip()[0:2] if x[0] == "-" else x[0:2]).lower()
	if x[0] == x[-1] == '"' :
		return ("vm_dword_t", s.strip("\"'"))
	elif num_sig == "0x" :
		return __parse_num_lit(x, base=16, known_types=known_types)
	elif num_sig == "0d" :
		return __parse_num_lit(x, base=10, known_types=known_types)
	elif num_sig == "0o" :
		return __parse_num_lit(x, base=8, known_types=known_types)
	elif num_sig == "0b" :
		return __parse_num_lit(x, base=2, known_types=known_types)
	elif num_sig[0] in ".0123456789" :
		return __parse_num_lit(x)
	elif x[0] in "_abcdefghijklmnoprstuvwxyz" :
		if x in variables :
			return variables[x]
		else :
			return (None, x)
	else :
		raise Exception("can not parse value")


def compare_types(known_types, a, b) :
	"""
	a, b are type names, keys in known_types dict with type_t tuples
	"""
	return known_types[a].priority - known_types[b].priority


def infer_block_type(block, preds, types, known_types) :
	inferred = None
#	print(here(), block)
	for t, t_nr, preds in preds :
		if t.type_name == core.TYPE_INFERRED :
			inherited = types[block, t, t_nr]
#			print(here(), inherited)
			if inferred is None or compare_types(known_types, inherited, inferred) > 0 :
				inferred = inherited
#	return sorted(inherited,
#		cmp=partial(compare_types, known_types))[-1]

	return inferred


def __infer_types_pre_dive(g, delays, types, known_types, n, nt, nt_nr, m, mt, mt_nr, visited) :
	mt_type_name = mt.type_name
#	print(here(), n, nt, nt_nr, "<-", m, mt, mt_nr, "type:", mt_type_name)
	if mt_type_name == core.TYPE_INFERRED :
		if core.compare_proto_to_type(m.prototype, core.DelayOutProto) :
			value_type, _ = parse_literal(delays[m], known_types=known_types)
			mt_type_name = types[m, mt, mt_nr] = value_type
		elif core.compare_proto_to_type(m.prototype, core.ConstProto) :
			value_type, _ = parse_literal(m.value[0], known_types=known_types)
			mt_type_name = types[m, mt, mt_nr] = value_type
		else :
			types[m, mt, mt_nr] = mt_type_name = infer_block_type(m, g[m].p, types, known_types)
			if core.compare_proto_to_type(m.prototype, core.DelayOutProto) :
				pass
	if nt.type_name == core.TYPE_INFERRED :
		types[n, nt, nt_nr] = mt_type_name


def __infer_types_post_visit(g, types, known_types, n, visited) :
	p, s = g[n]
#	print(here(), n, s)
	for t, t_nr, succs in s :
		if not succs :
			types[n, t, t_nr] = infer_block_type(n, p, types, known_types)


def __inferr_types_dft_roots_sorter(g, roots) :
	return sorted(__dft_alt_roots_sorter(g, roots),
		key=lambda n: 0 if core.compare_proto_to_type(n.prototype, core.InitDelayOutProto) else 1)


def infer_types(g, expd_dels, known_types, allready_inferred=None) :
	"""
	types of outputs are inferred from types of inferred (in fact, inherited) inputs
	block with inferred output type must have at least one inferred input type
	if block have more than one inferred input type, highest priority type is used for all outputs
	type of Delay is derived from initial value
	optional allready_inferred contains types allready inferred in form { m, mt, mt_nr : type_name, ... }
	"""
	delays = {}
	for k, (din, dout) in expd_dels.items() :
		delays[din] = delays[dout] = k.value[0]
	types = {} if allready_inferred is None else allready_inferred

	dft_alt(g,
		post_dive=partial(__infer_types_pre_dive, g, delays, types, known_types),
		post_visit=partial(__infer_types_post_visit, g, types, known_types),
		roots_sorter=__inferr_types_dft_roots_sorter,
		sinks_to_sources=True)

	return types

# ------------------------------------------------------------------------------------------------------------

#TODO	__check_directions(conns)
def make_dag(model, meta, known_types, do_join_taps=True, delay_numbering_start=0) :
	conns0 = { k : v for k, v in model.connections.items() if v }
	model_blocks = tuple(b for b in model.blocks if not core.compare_proto_to_type(b.prototype, core.TextAreaProto))
	blocks, conns1, delays = __expand_delays(model_blocks, conns0, delay_numbering_start)

	conns_rev = reverse_dict_of_lists(conns1, lambda values: list(set(values)))
	graph = { b : adjs_t(
			[ (t, n, conns_rev[(b, t, n)] if (b, t, n) in conns_rev else []) for t, n in in_terms(b) ],
			[ (t, n, conns1[(b, t, n)] if (b, t, n) in conns1 else []) for t, n in out_terms(b) ])
		for b in blocks }

	is_sane = __dag_sanity_check(graph, stop_on_first=False)
	if not is_sane :
		raise Exception(here() + ": produced graph is insane")

	__expand_joints_new(graph)

	if do_join_taps :
		join_taps(graph)

	return graph, delays

# ------------------------------------------------------------------------------------------------------------

def __dft_alt_roots_sorter(g, roots) :
	comps = {}
	for comp in graph_components(g) :
		hsh = md5()
		comp_loc_ids = { n : location_id(g, n, term=None) for n in comp }
		for m in sorted(comp, key=lambda n: comp_loc_ids[n]) :
			hsh.update(comp_loc_ids[m].encode())
		comps.update({ n : hsh.hexdigest() for n in comp})

	sortable = sortable_sinks(g, roots)
#	print(here(), "sortable=", sortable, "comps=", comps)

#	def comparer(a, b) :
#		per_comp = cmp(comps[a], comps[b])
#		return per_comp if per_comp else cmp(sortable[a], sortable[b])
#	return sorted(sortable, cmp=comparer)

	return sorted(sortable, key=lambda x: comps[x]+"_"+sortable[x])


def __dft_alt_term_sorter(g, block, preds) :
	for t, t_nr, neighbours in preds :
		if len(neighbours) > 1 :
#TODO TODO TODO
#			print("__dft_alt_term_sorter:", neighbours, "sort needed")
			lid = location_id(g, block, term=(t, t_nr))
			keys = { (b, mt, nr) : location_id(g, b, term=(mt, nr)) for b, mt, nr in neighbours }
			neighbours_list = sorted(neighbours, key=lambda i: keys[i])
		else :
			neighbours_list = neighbours

#		neighbours_list = neighbours

		for b, mt, nr in neighbours : #XXX
			yield t, t_nr, b, mt, nr

# ------------------------------------------------------------------------------------------------------------

def __sort_sinks_post_dive(hsh, n, nt, nt_nr, m, mt, mt_nr, visited) :
	edge = (n.to_string(), ".", nt.name, "/", str(nt_nr),
		"<-", m.to_string(), ".", mt.name, "/", str(mt_nr))
#	print("\t", "".join(edge))
	hsh.update("".join(edge).encode())


def location_id(g, block, term=None) :
	assert(term==None or (term!=None and len(term) == 2))
	hsh = md5()
	dft(g, block, undirected=True,
		post_dive=partial(__sort_sinks_post_dive, hsh), term=term)
	digest = hsh.hexdigest()
	return digest


def sortable_sinks(g, sinks) :
	sortable = {}	
	for s in sinks :
		digest = location_id(g, s, term=None)
		sortable[s] = digest
	return sortable

# ------------------------------------------------------------------------------------------------------------

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

def __where_to_go(neighbourhood, sinks_to_sources, undirected) :
	if undirected :
		return neighbourhood.p + neighbourhood.s
	elif sinks_to_sources :
		return neighbourhood.p
	else :
		return neighbourhood.s


def __dft_alt_nr_tree(g, root, pre_visit, pre_dive, post_dive, post_visit,
		sort_successors, visited, sinks_to_sources, undir, term_list=None) :

#	terms = list(__dft_alt_term_sorter(g, root, __where_to_go(g[root], sinks_to_sources, undir)))
#	pre_visit(root, visited, terms)
#	stack = [ (root, None, terms.__iter__()) ]

	if term_list == None :
		terms = list(__dft_alt_term_sorter(g, root, __where_to_go(g[root], sinks_to_sources, undir)))
	else :
		terms = list(__dft_alt_term_sorter(g, root,
			[ (term_list[0], term_list[1], []) ]))
#		terms = [ term_list ]
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
			((nt, nt_nr, m, mt, mt_nr), ) = islice(it, 1)
			stack[-1] = n, (nt, nt_nr, m, mt, mt_nr), it
			pre_dive(n, nt, nt_nr, m, mt, mt_nr, visited)
			if not m in visited :
				visited[m] = True
				terms = list(__dft_alt_term_sorter(g, m, __where_to_go(g[m], sinks_to_sources, undir)))
#				print "\t", here(), m
				pre_visit(m, visited, terms)
				stack.append((m, None, terms.__iter__()))
		except ValueError : #StopIteration :
			stack.pop(-1)
			post_visit(n, visited)


def dft(g, v,
		pre_visit = lambda *a, **b: None,
		pre_dive = lambda *a, **b: None,
		post_dive = lambda *a, **b: None,
		post_visit = lambda *a, **b: None,
		sort_successors = lambda *a, **b: None,
		sinks_to_sources=True,
		undirected=False,
		visited={},
		term=None) :
	"""
	graph structure:
	{
		blockA :
			(p=[ (blockA->term, blockA->term->term_number,
				[ (blockB, blockB->term, blockB->term->term_number ] ), ... ],
			 s=[ ]), ...
	}
	"""

	visited[v] = True
	term_list = None
	if term != None :
		t, t_nr = term
		(term_list, ) = [ (t, t_nr, nbh) for t, t_nr, nbh in
			__where_to_go(g[v], sinks_to_sources, undirected) if (t, t_nr) == term]
	return __dft_alt_nr_tree(g, v, pre_visit, pre_dive, post_dive,
		post_visit, sort_successors, visited, sinks_to_sources, undirected, term_list=term_list)

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
		dft(g, v,
			pre_visit = pre_visit,
			pre_dive = pre_dive,
			post_dive = post_dive,
			post_visit = post_visit,
			sinks_to_sources=sinks_to_sources,
			undirected=False,
			visited=visited) 
		post_tree(v, visited)

# ------------------------------------------------------------------------------------------------------------

def graph_components(g) :
	comps = []
	visited = {}
	for v in g.keys() :
		comp = {}
		if not v in visited :
			dft(g, v, undirected=True, visited=comp)
			visited.update(comp)
			comps.append(comp.keys())
	return comps

# ------------------------------------------------------------------------------------------------------------

def __su_get_number(numbering, src_blocks_tuple) :
	t, nr, src_b, i = src_blocks_tuple
	return numbering[src_b][0]


def __su_post_visit(g, numbering, n, visited) :
#TODO add documentation
#TODO take into account temp variables?
	"""
	commutativity comes in two flavours, it may be commutative block,
	or numbered instances of variadic terminal
	"""

#	print here(), n

	p, s = g[n] # XXX s might be used to analyze spill space usage
	src_blocks1 = [ (t, nr, src_b, i) for ((t, nr, ((src_b, src_t, src_t_nt),)), i) in zip(p, count()) ]
	src_blocks1.sort(key=lambda sb : __su_get_number(numbering, sb))
	if n.prototype.commutative :
#		src_grouped = [ ( None, sorted(src_blocks1, key=lambda sb : __su_get_number(numbering, sb)) ) ]
		src_grouped = [ ( None, src_blocks1 ) ]
#		src_grouped_old = [ ( None, sorted(src_blocks1, key=lambda (t, nr, src_b, i) : -numbering[src_b][0]) ) ]
#		print here(), src_grouped_old == src_grouped
	else :
#		print here()
#		src_grouped = [ (t, list(rest)) for t, rest in groupby(src_blocks1, lambda (term, _0, _1, _2): term) ]
		src_grouped = [ (t, list(rest)) for t, rest in groupby(src_blocks1, lambda sb: sb[0]) ]
	index = 0
	evaluated_blocks = []
	usages = []
	indices = []
	for group_term, src_blocks in src_grouped :
		if not n.prototype.commutative and group_term.commutative:
#			src_blocks_old = sorted(src_blocks, key=lambda (t, nr, src_b, i) : -numbering[src_b][0])
			src_blocks.sort(key=lambda sb : __su_get_number(numbering, sb))
#			print(here(), src_blocks_old == src_blocks)

		for term, nr, src_b, i in src_blocks :
			if not src_b in evaluated_blocks :
#				print here(), numbering, src_b
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
	print(here())
	numbering = {}
	dft_alt(g, post_visit = partial(__su_post_visit, g, numbering))
	return numbering


# ------------------------------------------------------------------------------------------------------------


def temp_init(known_types) :
	tmp = { tp_name : []
		for tp_name in known_types if not tp_name in (core.TYPE_VOID, core.TYPE_INFERRED) }
	return tmp


def get_tmp_slot(tmp, slot_type=None) :
	assert(not slot_type is None)
	if "empty" in tmp[slot_type] :
		slot = tmp[slot_type].index("empty")
	else :
		slot = len(tmp[slot_type])
		tmp[slot_type].append("empty")
	return slot


def add_tmp_ref(tmp, refs, slot_type=None) :
	assert(not slot_type is None)
	assert(len(refs)>0)
	assert(slot_type != core.TYPE_INFERRED)
	slot = get_tmp_slot(tmp, slot_type=slot_type)
	tmp[slot_type][slot] = list(refs)
	return slot


def pop_tmp_ref(tmp, b, t, t_nr) :
	for slot_type, t_tmp in tmp.items() :
		for slot, nr in zip(t_tmp, count()) :
			if slot != "empty" and (b, t, t_nr) in slot :
				slot.remove((b, t, t_nr))
				if len(slot) == 0 :
					t_tmp[nr] = "empty"
				return slot_type, nr
	return None


def tmp_used_slots(tmp) :
	"""
	returns current number of non-empty slots of all types
	"""
	return sum([ sum([ 1 for slot in t_tmp if slot != "empty" ])
		for tp, t_tmp in tmp.items() ])


def tmp_max_slots_used(tmp, slot_type=None) :
	"""
	returns peak number of slots in use to this time
	returns results for single data type if slot_type argument set
	"""
	slots = [ t_tmp for tp, t_tmp in tmp.items()
		if slot_type == None or tp == slot_type ]
	return sum([ sum([ 1 for slot in t_tmp ]) for t_tmp in slots ])


def tmp_merge(tmp0, tmp1) :
	tmp = dict(tmp1)
	for t, slots in tmp0.items() :
		if t in tmp :
			tmp[t].extend(slots)
		else :
			tmp[t] = slots
	return tmp

# ------------------------------------------------------------------------------------------------------------


def init_pipe_protos(known_types) :
#TODO generalize for other IPC schemes
	g_protos = {}
	for type_name in known_types :
		if type_name != core.TYPE_INFERRED :
			gw_proto = core.GlobalWriteProto(type_name)
			gr_proto = core.GlobalReadProto(type_name)
			g_protos[type_name] = (gw_proto, gr_proto)
	return g_protos


def extract_pipes(g, known_types, g_protos, pipe_replacement) :
	pipes = { n for n in g if core.compare_proto_to_type(n.prototype, core.PipeProto) }
	for n in pipes :
		pipe_name = block_value_by_name(n, "Name")
		pipe_default = block_value_by_name(n, "Default")
		pipe_type, v = parse_literal(pipe_default, known_types=known_types, variables={})
		gw_proto, gr_proto = g_protos[pipe_type]
		pipe_replacement[pipe_name] = (pipe_type, pipe_default, gw_proto, gr_proto)
	#TODO maybe return something useful for generation of globals


def replace_pipes(g, g_protos, pipe_replacement) :
	pipe_ends = { n : block_value_by_name(n, "Name") for n in g if core.compare_proto_to_type(n.prototype, core.PipeEndProto) }

	unmatched = [ pe for pe in pipe_ends
		if not (block_value_by_name(pe, "Name") in pipe_replacement) ]
	if unmatched :
		raise Exception("unmatched pipes found! {0}".format(str(unmatched)))

	pipes = { n for n in g if core.compare_proto_to_type(n.prototype, core.PipeProto) }

	for n in pipes :
		pipe_name = block_value_by_name(n, "Name")
		pipe_type, pipe_default, gw_proto, gr_proto = pipe_replacement[pipe_name]
		gw_proto, gr_proto = g_protos[pipe_type]
		m = dfs.BlockModel(gw_proto, "itentionally left blank")
		m.value = (pipe_name, )
		replace_block(g, n, m)

	for pipe_end, pipe_name in pipe_ends.items() :
		pipe_type, pipe_default, gw_proto, gr_proto = pipe_replacement[pipe_name]
		m = dfs.BlockModel(gr_proto, "itentionally left blank")
		m.value = (pipe_name, )
		replace_block(g, pipe_end, m)


# ------------------------------------------------------------------------------------------------------------


def __expand_macro(g, library, n, known_types, cache, local_block_sheets) :
	name = n.prototype.exe_name
	full_name = n.prototype.library + "." + name

#	print here(), full_name

	sheet = None
	if n.prototype.library == "<local>" :
#		print here(), full_name
		sheet_name = "@macro:" + name
		if sheet_name in local_block_sheets :
			sheet = core.clone_sheet(local_block_sheets[sheet_name][1], library)
	else :
		sheet = core.load_library_sheet(library, full_name, "@macro:" + name)

	if sheet is None :
		raise Exception("failed to expand macro '" + full_name + "'")

	offset = reduce(max, (b.nr for b in g if core.compare_proto_to_type(b.prototype, core.DelayInProto)), 0)#TODO
	gm, delays = make_dag(sheet, None, known_types, do_join_taps=False, delay_numbering_start=offset+1)

#TODO
#	print here(), full_name, full_name in cache
#	if full_name in cache :
#		block = cache[full_name]
#	else :
#		block = __instantiate_macro(library, full_name)
#		cache[full_name] = block

	inputs = { b.value[0] : (b, s[0][2]) for b, (_, s) in gm.items() if core.compare_proto_to_type(b.prototype, core.InputProto) }
	outputs = { b.value[0] : (b, p[0][2]) for b, (p, _) in gm.items() if core.compare_proto_to_type(b.prototype, core.OutputProto) }

	for io_blocks in (inputs, outputs) :
		for io, _ in io_blocks.values() :
			remove_block(gm, io)

	p, s = g[n]

	#XXX to handle variadic terms map p -> inputs

	map_in = { (it, it_nr) : tuple((b, t, nr) for b, t, nr in inputs[it.name][1])
		for it, it_nr, _ in p }
	map_out = { (ot, ot_nr) : tuple((b, t, nr) for b, t, nr in outputs[ot.name][1])
		for ot, ot_nr, _ in s }

	remove_block_and_patch(g, n, gm, map_in, map_out)

	return (delays, )


def expand_macroes(g, library, known_types, local_block_sheets, block_cache=None) :
	cache = block_cache_init() if block_cache is None else block_cache
	new_delays = {}
	prev_batch = set()
	macroes = { b for b in g if core.compare_proto_to_type(b.prototype, core.MacroProto) }
	while macroes != prev_batch :
		for n in sorted(macroes) :
			delays, = __expand_macro(g, library, n, known_types, cache, local_block_sheets)
			new_delays.update(delays)
		prev_batch = set(macroes)
		macroes = { b for b in g if core.compare_proto_to_type(b.prototype, core.MacroProto) }
	if macroes :
		raise Exception("failed to {0} expand macroes".format(len(macroes)))
	return (new_delays, )


def block_cache_init() :
	return {}


# ------------------------------------------------------------------------------------------------------------


def __check_for_cycles_post_visit(n, visited) :
	pass


def check_for_cycles(g) :
	"""
	return possibly incomplete list of cycles in graph g
	"""
	pass


# ------------------------------------------------------------------------------------------------------------


def create_function_call(name) :
	"""
	return block instance calling c function <name> with zero arguments
	"""
	block = dfs.BlockModel(core.FunctionCallProto(), "itentionally left blank")
	block.value = (name, )
	return block


#probably not needed anymore
#def implement_dfs(model, meta, codegen, known_types, out_fobj) :
#	graph, delays = make_dag(model, meta, known_types)
#	types = infer_types(graph, delays, known_types=known_types)
#	libs_used = {}
#	code = codegen.codegen_alt(graph, delays, {}, libs_used, types)
#	out_fobj.write(code)#XXX pass out_fobj to codegen?


def process_sheet(dag, meta, known_types, lib, local_block_sheets, block_cache, g_protos, pipe_replacement) :

	graph, delays = dag

	new_delays, = expand_macroes(graph, lib, known_types, local_block_sheets, block_cache=block_cache)
	delays.update(new_delays)
	join_taps(graph)
	types = infer_types(graph, delays, known_types=known_types)
	extract_pipes(graph, known_types, g_protos, pipe_replacement)

	return graph, delays, meta, types


def pipe_replacement_to_glob_vars(items) :
	"""
	generate list of global variable tuples from pipe_replacement dictionary
	"""
	glob_vars = [ (pipe_name, pipe_type, pipe_default)
		for pipe_name, (pipe_type, pipe_default, gw_proto, gr_proto) in items.items() ]
	return glob_vars


def include_list(library, libraries_used) :
	"""
	generate list of includes from library object and set of libs used
	"""
	include_files = []
	for l in library.libs :
		if l.name in libraries_used :
			include_files.extend(l.include_files)#TODO maybe use only file name
	return include_files


def check_delay_numbering(graph_data) :
	"""
	basic check of delay numbering, like errors when instantiating macroes
	"""
	for _, _, dels, _, _ in graph_data :
		del_check = tuple((i.nr, i.nr==o.nr) for d, (i, o) in dels.items())
		yield all(nr_eq for _, nr_eq in del_check)
		yield len(del_check)==len({nr for nr, _ in del_check})


def simple_entry_point_stub(user_function, call_setup) :
	"""
	create graph stub for simple entry point function
	"""
	loop_call = create_function_call(user_function)
	init_call = create_function_call("init")
	main_tsk_g = { loop_call : adjs_t([], []),  init_call : adjs_t([], [])  }
	first_call = loop_call
	if call_setup :
		setup_call = create_function_call("setup")
		main_tsk_g[setup_call] = adjs_t([], [])
		chain_blocks(main_tsk_g, setup_call, loop_call)
		first_call = setup_call
	chain_blocks(main_tsk_g, init_call, first_call)

	main_tsk_meta = { "endless_loop_wrap" : False}

	return "main", main_tsk_g, {}, main_tsk_meta, {}


def parse_task_period(s) :
	"""
	parse task period string and return period in ms or "idle"
	"""
#TODO use parse_literal
	p = s.strip().lower()
#	print here(), s
	if p.endswith("ms") :
		return int(p[0:-2])
	elif p.endswith("s") :
		return 1000 * int(p[0:-1])
	elif p == "idle" :
		return "idle"
	else :
		return None


def implement_workbench(w, sheets, w_meta, codegen, known_types, lib, out_fobj) :
	"""
	sheets = { name : sheet, ... }
	"""

	global_meta = dict(w_meta)

	special_sheets = { "@setup" } #TODO interrupts; would be dict better?
	special = { name : s for name, s in sheets.items() if name.strip()[0] == "@" }
	unknown = [ name for name in special
		if (not name in special_sheets) and (core.sheet_block_name_and_class(name) is None) ]
	if unknown :
		raise Exception("Unknown special sheet name(s) '{0}'".format(unknown))

	g_protos = init_pipe_protos(known_types)
	pipe_replacement = {}
	graph_data = []
	block_cache = block_cache_init()

	tsk_setup_meta = { "endless_loop_wrap" : False }#TODO, "function_wrap" : False, "is_entry_point" : False }

	local_block_sheets = {}
	for name, sheet_list_iter in groupby(sorted(special.items(), key=lambda x: x[0]), key=lambda x: x[0]) :
		if core.is_macro_name(name) or core.is_function_name(name) :
			sheet_list = tuple(sheet_list_iter)
#			print here(), name, sheet_list
			assert(len(sheet_list)==1)
			local_block_sheets[name], = sheet_list

	for name, sheet_list in groupby(sorted(special.items(), key=lambda x: x[0]), key=lambda x: x[0]) :
		#TODO handle multiple special sheets of same type
		if name == "@setup" :
			tsk_name = name.strip("@")
			(_, s), = tuple(sheet_list)
			dag = make_dag(s, None, known_types, do_join_taps=False)
			g_data = process_sheet(dag, tsk_setup_meta, known_types, lib,
				local_block_sheets, block_cache, g_protos, pipe_replacement)
			graph_data.append((tsk_name, ) + g_data)
		elif core.is_macro_name(name) :
#			print here(), name
			pass
		elif core.is_function_name(name) :
#			print here(), name
			pass
		else :
			raise Exception("impossible exception")

	periodic_sched = True

	if not periodic_sched :
		l = [ make_dag(s, None, known_types, do_join_taps=False)
			for name, s in sorted(sheets.items(), key=lambda x: x[0])
			if not name in special ]
		g_data = process_sheet(dag_merge(l), {}, known_types, lib, local_block_sheets, block_cache, g_protos, pipe_replacement)
		graph_data.append(("loop", ) + g_data)
	else :
		tsk_groups = {}
		global_meta["periodic_sched"] = True
		tsk_sheets = ((tsk_name, s)
			for tsk_name, s in sorted(sheets.items(), key=lambda x: x[0])
			if not tsk_name in special)
		for tsk_name, s in tsk_sheets :
#XXX mangle/pre/postfix tsk_name
			dag = make_dag(s, None, known_types, do_join_taps=False)
			meta = dict(s.get_meta())
			if "task_period" in meta :
				tsk_period = parse_task_period(meta["task_period"])
			else :
				tsk_period = "idle"
			if not tsk_period in tsk_groups :
				tsk_groups[tsk_period] = []
			tsk_groups[tsk_period].append(tsk_name)
			meta["endless_loop_wrap"] = False
			meta["function_attributes"] = "inline"
			meta["state_vars_scope"] = "local"#"module"
			meta["state_vars_storage"] = "heap"
			g_data = process_sheet(dag, meta, known_types, lib,
				local_block_sheets, block_cache, g_protos, pipe_replacement)
			graph_data.append((tsk_name, ) + g_data)

#	print here(), tsk_groups

	graph_data.append(simple_entry_point_stub("loop", "@setup" in special))

	assert(all(check_delay_numbering(graph_data)))

	tsk_cg_out = []
	libs_used = set()
	pipe_vars = {}
	for tsk_name, g, d, meta, types in graph_data :
		replace_pipes(g, g_protos, pipe_replacement)
		tsk_cg_out.append(codegen.codegen(g, d, meta,
			types, known_types, pipe_vars, libs_used, task_name=tsk_name))

	include_files = include_list(lib, libs_used)

	glob_vars = pipe_replacement_to_glob_vars(pipe_replacement)

	codegen.churn_code(global_meta, glob_vars, tsk_cg_out, include_files, tsk_groups, out_fobj)

	#TODO say something about what you've done
	return libs_used,

# ------------------------------------------------------------------------------------------------------------

def main() :
	"""
	standalone entry point, looking for arguments in sys.argv
	"""
#	import argparse
#	parser = argparse.ArgumentParser(description="bloced")
#	parser.add_argument("file", metavar="fname", type=str, nargs=1,
#                   help="input file")
#	args = parser.parse_args()
#	fname = args.file[0]
	import serializer

	if len(sys.argv) != 3 :
		print("expected exactly 2 arguments")
		exit(100)

	action = sys.argv[1]
	fname = os.path.abspath(sys.argv[2])

	if os.path.splitext(fname)[1].lower() != ".w" :#TODO path separator
		print("formats other than .w are not supported anymore")
		exit(1)

	main_lib = core.create_block_factory(scan_dir=os.path.join(os.getcwd(), "library"))#TODO multiple search dirs
	local_lib = core.BasicBlocksFactory(load_basic_blocks=False)
	local_lib.load_standalone_workbench_lib(fname, "<local>")
#	print here(), local_lib.block_list
	library = core.SuperLibrary([main_lib, local_lib])

	w = dfs.Workbench(
#		lib_dir=os.path.join(os.getcwd(), "library"),
		passive=True)

#	library = w.blockfactory

	try :
		with open(fname, "rb") as f :
			serializer.unpickle_workbench(f, w, use_cached_proto=False, library=library)
	except :
		print("error loading workbench file")
		raise
#		exit(666)
	sheets = w.sheets
	global_meta = w.get_meta()

	if action == "c" :
		import ccodegen as cg
	elif action == "f" :
		import fcodegen as cg
	else :
		exit(666)

	implement_workbench(w, sheets, global_meta, cg, core.KNOWN_TYPES, library, sys.stdout)

# ------------------------------------------------------------------------------------------------------------

if __name__ == "__main__" :
	main()


