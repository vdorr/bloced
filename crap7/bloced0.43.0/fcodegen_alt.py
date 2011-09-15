
import dfs
from os import linesep
import string
#from functools import partial
from itertools import groupby, chain, product, islice, dropwhile, count#, imap, ifilter, izip
from pprint import pprint

# ------------------------------------------------------------------------------------------------------------

# convention: get_terms - last term in list is on top of stack
# assumption : every block is evaluated exactly once per iteration
#	- except constants
#	- evaluation of stateless components can (should) be optimized

# ------------------------------------------------------------------------------------------------------------

def __execute(code, v) :
	if isinstance(v.prototype, dfs.DelayInProto) :
		code.append("to del%i" % v.nr)
	elif isinstance(v.prototype, dfs.DelayOutProto) :
		code.append("del%i" % v.nr)
	else :
		code.append(v.prototype.exe_name)

# ------------------------------------------------------------------------------------------------------------

def __gather_inputs(g, code, r, d, tmp, const, conns, v, inputs) :
	for t in inputs :
		if (v, t) in const :
			code.append(const.pop((v, t)))
		else :
			(slot_value, slot), = tuple(islice(dropwhile(lambda temp: not (v, t) in temp[0],
				zip(tmp, count())), 0, 1))
			code.append("tmp%i" % slot)
			#TODO tmp[slot] = ("empty",) if slot_value == (v, t) else slot_value - (v, t)
			#TODO tmp[slot] -= set((v, t))
			slot_value.remove((v, t))
			if not slot_value :
				tmp[slot] = ("empty",)

# ------------------------------------------------------------------------------------------------------------

def __manage_outputs(g, code, r, d, tmp, conns, v, outputs, still_needed) :
	for t in reversed(outputs) :
		if t in still_needed :
			if ("empty",) in tmp :
				slot = tmp.index(("empty",))
			else :
				slot = len(tmp)
				tmp.append(("empty",))
			tmp[slot] = list(conns[(v, t)])
			code.append("to tmp%i" % slot)
		else :
			code.append("drop")

# ------------------------------------------------------------------------------------------------------------

def codegen(g, conns, expd_dels, tsorted) :
	s = list(tsorted)
	code = []
	r = []
	d = []
	const = {}
	tmp = []

#	print "s"; pprint(s); print "conns"; pprint(conns)
	
	del_in = filter(lambda b: isinstance(b.prototype, dfs.DelayInProto), s)
	del_out = filter(lambda b: isinstance(b.prototype, dfs.DelayOutProto), s)
	#XXX in: out OR in: [out,] ? a) seem to be simpler to implement
	assert(list(set(del_in)) == del_in)
	assert([ i.nr for i in del_in ] == list(set([o.nr for o in del_out])) )
	delays = dict([ (i, filter(lambda o: o.nr == i.nr, del_out)) for i in del_in ]) #TODO test
	
	for i, outs in delays.iteritems() :
		#assert(s.index(i) > last_del_out_index)
		del_in_index = s.index(i)
		last_del_out_index = max([ s.index(o) for o in outs ])
		if del_in_index < last_del_out_index :
			s.insert(del_in_index, s.pop(last_del_out_index))

#	const = dict(chain(*
#		[ [ (cn, v.value) for cn in conns[(v, v.terms[0])] ]
#			for v in ifilter(lambda v: isinstance(v.prototype, dfs.ConstProto), s)]))
	const = dict(chain(*
		[ [ (cn, v.value) for cn in conns[(v, v.terms[0])] ]
			for v in s if isinstance(v.prototype, dfs.ConstProto)]))

#	for v in ifilter(lambda v: not isinstance(v.prototype, dfs.ConstProto), s) :
	for v in [ v for v in s if not isinstance(v.prototype, dfs.ConstProto) ] :
		loc = []
		inputs = filter(lambda t: t.direction == dfs.INPUT_TERM, v.terms)
		__gather_inputs(g, loc, r, d, tmp, const, conns, v, inputs)
		__execute(loc, v)
		outputs = filter(lambda t: t.direction == dfs.OUTPUT_TERM, v.terms)
		still_needed = filter(lambda t: (v, t) in conns, outputs)
		__manage_outputs(g, loc, r, d, tmp, conns, v, outputs, still_needed)
		code.append(string.join(loc, " "))

	del_init = [ "%i " % int(d.value) for d in sorted(expd_dels.keys(), lambda x,y: y.nr-x.nr) ]

	return (": tsk" + linesep +
		# locals and delays
		"\t" + "".join(del_init) + ("0 " * len(tmp)) + linesep +
		"\tlocals| " + ("del%i " * len(del_init)) % tuple(range(len(del_init))) +
		("tmp%i " * len(tmp)) % tuple(range(len(tmp))) + "|" + linesep +
		# main loop
		"\tbegin" + linesep +
		string.join([ "\t\t" + loc for loc in code ], linesep) + linesep +
		"\tagain" + linesep + ";")

# ------------------------------------------------------------------------------------------------------------




def codegen(g, expd_dels) :
	l = []

	tmp = []
	d_stack = []
	code = ""

	const = dict(chain(*
		[ [ (cn, v.value) for cn in conns[(v, v.terms[0])] ]
			for v in s if isinstance(v.prototype, dfs.ConstProto)]))

	def pre_visit(n) :
		pass#nothing? really?

	def post_visit(n) :

		#gather inputs
		for in_term, outputs in g[n].p :#XXX not reversed?
			for sb, st in outputs :
				if isinstance(sb.prototype, dfs.ConstProto) :
					#push
					pass
#				elif d_stack and d_stack[-1] == (sb, st) :
				elif (sb, st) in d_stack :
					stack_pos = d_stack.index((sb, st))
					if stack_pos > 0 :
					pass#nothing to do
				elif (sb, st) in temp :
					(slot_value, slot), = tuple(islice(dropwhile(lambda temp: not (v, t) in temp[0],
						zip(tmp, count())), 0, 1))
					code.append("tmp%i" % slot)
					#TODO tmp[slot] = ("empty",) if slot_value == (v, t) else slot_value - (v, t)
					#TODO tmp[slot] -= set((v, t))
					slot_value.remove((v, t))
					if not slot_value :
						tmp[slot] = ("empty",)

		__execute(code, n)

		#manage outputs
		for out_term, inputs in g[n].s :
			if len(inputs) > 1 :
				#>r
				pass
			for tb, tt in sources :
				if t in still_needed :
					if ("empty",) in tmp :
						slot = tmp.index(("empty",))
					else :
						slot = len(tmp)
						tmp.append(("empty",))
					tmp[slot] = list(conns[(v, t)])
					code.append("to tmp%i" % slot)
				else :
					code.append("drop")


		l.append(n)

	def pre_tree(n) :
		expression = ""

	def post_tree(n) :
		print "post_tree:", expression

	dft_alt(g, pre_visit, post_visit, pre_tree, post_tree)
#	pprint(l)
	return "/* no code generated */"

# ------------------------------------------------------------------------------------------------------------

