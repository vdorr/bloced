
import dfs
from os import linesep
import string
#from functools import partial
from itertools import groupby, chain, product, ifilter, islice, dropwhile, izip, count
from pprint import pprint

# ------------------------------------------------------------------------------------------------------------

# convention: get_terms - last term in list is on top of stack
# assumption : every block is evaluated exactly once per iteration
#	- except constants
#	- evaluation of stateless components can (should) be optimized

# ------------------------------------------------------------------------------------------------------------

def __execute(code, v) :
	if isinstance(v.prototype, dfs.DelayInProto) :
		code.append("to delay%i" % v.nr)
	elif isinstance(v.prototype, dfs.DelayOutProto) :
		code.append("delay%i" % v.nr)
	else :
		code.append(v.prototype.get_type_name())

# ------------------------------------------------------------------------------------------------------------

def __gather_inputs(g, code, r, d, tmp, const, conns, v, inputs) :
	for t in inputs :
		if (v, t) in const :
			code.append(const.pop((v, t)))
		else :
			#slot_value = filter(lambda temp: (v, t) in temp, tmp)[0]#TODO use tuple(islice(dropwhile(

#			(slot_value, ) = tuple(islice(dropwhile(lambda temp: not (v, t) in temp, tmp), 0, 1))
#			slot = tmp.index(slot_value)

			(slot_value, slot), = tuple(islice(dropwhile(lambda temp: not (v, t) in temp[0],
				izip(tmp, count())), 0, 1))

			slot_value.remove((v, t))
			code.append("tmp%i" % slot)
			if not slot_value :
				tmp[slot] = "empty"

# ------------------------------------------------------------------------------------------------------------

def __manage_outputs(g, code, r, d, tmp, conns, v, outputs, still_needed) :
	for t in reversed(outputs) :
		if t in still_needed :
			if "empty" in tmp :
				slot = tmp.index("empty")
			else :
				slot = len(tmp)
				tmp.append("empty")
			tmp[slot] = list(conns[(v, t)])
			code.append("to tmp%i" % slot)
		else :
			code.append("drop")

# ------------------------------------------------------------------------------------------------------------

def codegen(g, conns, expd_dels, s) :
	code = []
	r = []
	d = []
	const = {}
	tmp = []

	print "s"; pprint(s); print "conns"; pprint(conns)
	
	del_in = filter(lambda b: isinstance(b.prototype, dfs.DelayInProto), s)
	del_out = filter(lambda b: isinstance(b.prototype, dfs.DelayOutProto), s)
	#XXX in: out OR in: [out,] ? a) seem to be simpler to implement
	assert(list(set(del_in)) == del_in)
	assert([ i.nr for i in del_in ] == list(set([o.nr for o in del_out])) )
	delays = dict([ (i, filter(lambda o: o.nr == i.nr, del_out)) for i in del_in ]) #TODO test
	
	#TODO delay in/out order enforcement
	for i, outs in delays.iteritems() :
		for o in outs :
			#print i, o
			assert(s.index(i) > s.index(o))

	const = dict(chain(*
		[ [ (cn, v.get_value()) for cn in conns[(v, v.get_terms()[0])] ]
			for v in ifilter(lambda v: isinstance(v.prototype, dfs.ConstProto), s)]))

	for v in ifilter(lambda v: not isinstance(v.prototype, dfs.ConstProto), s) :
		inputs = filter(lambda t: t.direction == dfs.INPUT_TERM, v.get_terms())
		__gather_inputs(g, code, r, d, tmp, const, conns, v, inputs)
		__execute(code, v)
		outputs = filter(lambda t: t.direction == dfs.OUTPUT_TERM, v.get_terms())
		still_needed = filter(lambda t: (v, t) in conns, outputs)
		__manage_outputs(g, code, r, d, tmp, conns, v, outputs, still_needed)

	del_init = [ "%i " % int(d.value) for d in sorted(expd_dels.keys(), lambda x,y: y.nr-x.nr) ]

	return (": tsk" + linesep +
		# locals and delays
		"\t" + "".join(del_init) + ("0 " * len(tmp)) + linesep +
		"\tlocals| " + ("delay%i " * len(del_init)) % tuple(range(len(del_init))) +
		("tmp%i " * len(tmp)) % tuple(range(len(tmp))) + "|" + linesep +
		# main loop
		"\tbegin" + linesep +
		string.join([ "\t\t" + loc for loc in code ], linesep) + linesep +
		"\tagain" + linesep + ";")

# ------------------------------------------------------------------------------------------------------------

