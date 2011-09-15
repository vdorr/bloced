
from dfs import *
from collections import namedtuple
from functools import partial
from itertools import groupby, chain, product
from pprint import pprint

# 1) preprocess :
#	- expand macroes
#	- convert joints to connections
#	- check consistency (i/o impedance)
# 2) separate connected components
# 3) find and break cycles
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

# ------------------------------------------------------------------------------------------------------------

def of_type(i, t) :
	return filter(lambda x: isinstance(x, t), i)

# ------------------------------------------------------------------------------------------------------------

def implement_dfs(model, meta) :
	ppmdl = __preproc(model, meta)
	graph, cycles, looseends = __tsort(ppmdl, meta)
	return impl_t(graph, cycles, looseends)

# ------------------------------------------------------------------------------------------------------------

def __ubft_int(g, v, f, visited) :
	adjlst = g[v]
	vtcs = adjlst.p.union(adjlst.s) - visited
	visited.update(vtcs)
	visit = list(vtcs)
	print "to be visited from", v, visit
	for vt in visit :
		f(vt)
	for vt in visit :
		__ubft_int(g, vt, f, visited)

def __ubft(g, v, f) :
	visited = set([v])
	__ubft_int(g, v, f, visited)
	print visited

def __components_visitor(blocks, comp, vt) :
	print vt
	if vt in blocks :
		blocks.remove(vt);
		comp.append(vt)

def __components(g) :
	blocks = list(g.keys())
	components = []
	while blocks :
		v = blocks.pop()
		comp = [ v ]
		print "part"
		__ubft(g, v, partial(__components_visitor, blocks, comp))
		if comp :
			components.append(comp)
	return components

def __replace_joint(blocks, conns, item) :
	pass

def __check_directions(conns) :
	return reduce(lambda x, item: x and item[0][1].direction == OUTPUT_TERM and
		reduce(lambda y, inp: y and inp[1].direction == INPUT_TERM, item[1], True),
			conns.items(), True)

def __preproc(model, meta) :
	blocks = model.get_blocks()
	conns = dict(filter(lambda item: item[1], model.get_connections().items()))
	#pprint(conns)

	print("__check_directions:", __check_directions(conns))
	
	s_dal = map(lambda g: (g[0],
		set(reduce(lambda a, i: a + map(lambda l: l[0], i[1]), g[1], [])) ),
		groupby(conns.items(), lambda x: x[0][0]))
	succs = s_dal + map(lambda v: (v, set([])), list(set(blocks) - set(map(lambda x: x[0], s_dal))))
	print("succs"); pprint(succs)
	
	# successors: expand g to one-to-one mapping, swap mappings and apply function above
	
	print "pgrps"
	pprint(list(groupby(reduce(lambda a, i: a + list(product(i[1], [i[0]])), succs, []), lambda x: x[0])))
	
	p_dal = map(lambda g: (g[0], set(map(lambda v: v[1], g[1]))),
		groupby(reduce(lambda a, i: chain(a, product(i[1], [i[0]])), succs, []), lambda x: x[0]))
	print("p_dal"); pprint(p_dal)	
	preds = p_dal + map(lambda v: (v, set([])), list(set(blocks) - set(map(lambda x: x[0], p_dal))))
	#pprint(preds)
	
	adjs = namedtuple("a", [ "p", "s", ])

	preds_dict = dict(preds)
	print("preds_dict"); pprint(preds_dict)
	g = dict(map(lambda i: (i[0], adjs(preds_dict[i[0]], i[1])), succs)) # this is our graph
	print("g"); pprint(g)

	components = __components(g)

	pprint(components)

	return None


	joints = filter(lambda b: isinstance(b.prototype, JointProto), blocks)
	print joints

#	- expand macroes
	#TODO

#	- convert joints to connections

	conns_without_joints = dict(map(partial(__replace_joint, blocks, conns), conns.items()))

	to_joint = filter(lambda c: isinstance(c[0][0].prototype, JointProto), conns.items())

	from_joint = filter(lambda c:
		reduce(lambda a, cn: a and isinstance(cn[1].prototype, JointProto), c[1], False),
			conns.items())

# ------------------------------------------------------------------------------------------------------------

def __joints2connections(model, meta) :
	pass

# ------------------------------------------------------------------------------------------------------------

def __find_cycles(model, meta) :
	pass

# ------------------------------------------------------------------------------------------------------------

def __tsort(model, meta) :
	return ( None, None, None, )

# ------------------------------------------------------------------------------------------------------------

