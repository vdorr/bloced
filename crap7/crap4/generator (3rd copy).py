
import dfs
import os
import string
from functools import partial
from itertools import groupby, chain, product
from pprint import pprint

# ------------------------------------------------------------------------------------------------------------

# convention: get_terms - last term in list is on top of stack

# ------------------------------------------------------------------------------------------------------------

def __execute(code, v) :
	if isinstance(v.prototype, dfs.DelayInProto) :
		code.append("to delay%i" % v.nr)
	elif isinstance(v.prototype, dfs.DelayOutProto) :
		code.append("delay%i" % v.nr)
	else :
		code.append(v.prototype.get_type_name())

# ------------------------------------------------------------------------------------------------------------

def __gather_inputs(g, code, r, d, tmp, state, const, conns, v, inputs) :
#	print "__gather_inputs", v.prototype.get_type_name()
#	print "tmp"; pprint(tmp)
#	print "const", const
#	print "state", state

	for t in inputs :
		if (v, t) in const :
			code.append(const.pop((v, t)))
		else :
#			print "xx", (v, t)
			#print state
			sta = filter(lambda d: (v, t) in d, state)#TODO use tuple(islice(dropwhile(
			if sta :
#				print "sta"
				code.append("delay%i" % state.index(sta[0]))
			else :
#				print "tmp", tmp
#				print "else:", (v, t)
				slot_value = filter(lambda temp: (v, t) in temp, tmp)[0]#TODO use tuple(islice(dropwhile(
				slot = tmp.index(slot_value)
				code.append("tmp%i" % slot)
				if not slot_value :
					tmp[slot] = "empty"

# ------------------------------------------------------------------------------------------------------------

def __manage_outputs(g, code, r, d, tmp, state, conns, v, outputs, still_needed) :
#	print "__manage_outputs", v, outputs
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

	state =666

	print "s"; pprint(s)
	print "conns"; pprint(conns)
	
	del_in = filter(lambda b: isinstance(b.prototype, dfs.DelayInProto), s)
	del_out = filter(lambda b: isinstance(b.prototype, dfs.DelayOutProto), s)
	assert(list(set(del_in)) == del_in)
	assert([ i.nr for i in del_in ] == list(set([o.nr for o in del_out])) )
	delays = dict([ (i, filter(lambda o: o.nr == i.nr, del_out)) for i in del_in ]) #TODO test

	for v in s :
		inputs = filter(lambda t: t.direction == dfs.INPUT_TERM, v.get_terms())
		__gather_inputs(g, code, r, d, tmp, state, const, conns, v, inputs)
		#TODO delay handling
		if v.prototype.get_type_name() == "Const" : # TODO move to __execute
			#print "const"
			for cn in conns[(v, v.get_terms()[0])] :
				const[cn] = v.get_value()
			continue
		else :
			__execute(code, v)
			
		outputs = filter(lambda t: t.direction == dfs.OUTPUT_TERM, v.get_terms())
		still_needed = filter(lambda t: (v, t) in conns, outputs)#XXX conns should not contain empty succs lists
		__manage_outputs(g, code, r, d, tmp, state, conns, v, outputs, still_needed)

	del_init = [ "%i " % int(d.value) for d in sorted(expd_dels.keys(), lambda x,y: y.nr-x.nr) ]

	locls = ("\tlocals| " + ("delay%i " * len(del_init)) % tuple(range(len(del_init))) +
		("tmp%i " * len(tmp)) % tuple(range(len(tmp))) + "|" + os.linesep)

	return (": tsk" + os.linesep + "\t" + "".join(del_init) + os.linesep + locls + "\tbegin" + os.linesep +
		string.join([ "\t\t" + loc for loc in code ], os.linesep) + os.linesep +
		"\tagain" + os.linesep + ";")

# ------------------------------------------------------------------------------------------------------------

