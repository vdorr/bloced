
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
	code.append(v.prototype.get_type_name())

# ------------------------------------------------------------------------------------------------------------

def __gather_inputs(g, code, r, d, tmp, state, const, conns, v, inputs) :
	print "__gather_inputs", v.prototype.get_type_name()
	print "tmp", tmp
	print "const", const
	print "state", state

	for t in inputs :
		if (v, t) in const :
			code.append(const.pop((v, t)))
		else :
			print "xx", (v, t)
			#print state
			sta = filter(lambda d: (v, t) in d, state)#TODO use tuple(islice(dropwhile(
			if sta :
				print "sta"
				code.append("delay%i" % state.index(sta[0]))
			else :
				print "tmp", tmp
				print "else:", (v, t)
				slot_value = filter(lambda temp: (v, t) in temp, tmp)[0]#TODO use tuple(islice(dropwhile(
				slot = tmp.index(slot_value)
				code.append("tmp%i" % slot)
				if not slot_value :
					tmp[slot] = "empty"

# ------------------------------------------------------------------------------------------------------------

def __manage_outputs(g, code, r, d, tmp, state, conns, v, outputs, still_needed) :
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

def codegen(g, conns, tsorted) :
	code = []
	r = []
	d = []
	const = {}
	tmp = []
	state = []

	print "tsorted", tsorted
	delays = filter(lambda b: isinstance(b.prototype, dfs.DelayProto), tsorted)
	s = filter(lambda b: not isinstance(b.prototype, dfs.DelayProto), tsorted)

#	pprint(conns)
	print "delays", delays

	state = map(lambda d: list(
		conns[d, filter(lambda t: t.direction == dfs.OUTPUT_TERM, d.get_terms())[0]]), delays)

	#XXX how is delay handled by tsort?!

	print "s", s

	for v in s :
		inputs = filter(lambda t: t.direction == dfs.INPUT_TERM, v.get_terms())
		__gather_inputs(g, code, r, d, tmp, state, const, conns, v, inputs)
		#TODO delay handling
		if v.prototype.get_type_name() == "Const" :
			#print "const"
			for cn in conns[(v, v.get_terms()[0])] :
				const[cn] = v.get_value()
		elif v.prototype.get_type_name() == "Delay" :
			#print "delay"
			pass #TODO
		else :
			#print "exec"
			__execute(code, v)
			
		outputs = filter(lambda t: t.direction == dfs.OUTPUT_TERM, v.get_terms())
		still_needed = filter(lambda t: (v, t) in conns, outputs)#XXX conns should not contain empty succs lists
		__manage_outputs(g, code, r, d, tmp, state, conns, v, outputs, still_needed)

	locls = (("%i " * len(delays)) % reversed(map(lambda d: d.get_value(), delays)) + os.linesep +
		"locals| " + ("delay%i " * len(delays)) % tuple(range(len(delays))) +
		("tmp%i " * len(tmp)) % tuple(range(len(tmp))) + "|" + os.linesep)

	return locls + string.join(code, os.linesep)

# ------------------------------------------------------------------------------------------------------------

