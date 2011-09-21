
import dfs
from dfs import INPUT_TERM, OUTPUT_TERM
import core
from os import linesep
import string
from functools import partial
from itertools import count, groupby
from pprint import pprint
from implement import *

# ------------------------------------------------------------------------------------------------------------

# execution
def __post_visit(g, code, tmp, subtrees, expd_dels, n, visited) :

#TODO can i get rid off som cycles by use of other callbacks?

	if isinstance(n.prototype, core.ConstProto) :
		return None # handled elsewhere

	inputs, outputs = g[n]
#	assert(outputs == g[n].s)
#	assert(inputs == g[n].p)

	args = []
	outs = []#TODO TODO TODO

#	print n

	#gather inputs
	for in_term, in_t_nr, preds in inputs :
		assert(len(preds)==1)
		((m, m_t, m_t_nr), ) = preds
#		print "\tgathering:", m, m_t, m_t_nr, "for", (n, in_term, in_t_nr), "subtrees:", subtrees
		if isinstance(m.prototype, core.ConstProto) :
			assert(m.value != None)
			args.append(str(m.value))
		elif (n, in_term, in_t_nr) in subtrees :
			args.append(subtrees.pop((n, in_term, in_t_nr)))
		else :
			slot = pop_tmp_ref(tmp, n, in_term, in_t_nr)
			if slot != None:
				args.append("tmp%i" % slot)
			else :
#				print tmp
				raise Exception("holy shit!")

	if len(outputs) > 0 :
		for out_term, out_t_nr, succs in outputs :
			#TODO outs!!!
#			print "out_term, out_t_nr, succs =", out_term, out_t_nr, succs
			if len(succs) > 0 :
				slot = add_tmp_ref(tmp, succs)
				outs.append("&tmp%i"%slot)
			else :
				outs.append("&dummy")

	if isinstance(n.prototype, core.DelayInProto) :
		del_in, del_out = expd_dels[n.delay]
		if not del_out in visited :
			slot = add_tmp_ref(tmp, [ (del_in, del_in.terms[0], 0) ])
			code.append("tmp%i = del%i" % (slot, n.nr))
#		code.append("to del%i" % n.nr)
		expr = "del%i=%s" % tuple([n.nr]+args)
	elif isinstance(n.prototype, core.DelayOutProto) :
		del_in, del_out = expd_dels[n.delay]
		if del_in in visited :
			slot = pop_tmp_ref(tmp, del_in, del_in.terms[0], 0)
			expr = "tmp%i" % slot
#			code.append("tmp%i" % slot)
		else :
			expr = "del%i" % n.nr
#			exe_name = "get_del%i" % n.nr
#			code.append("del%i" % n.nr)
#		exe_name = "get_del%i" % n.nr
	else :
		assert(n.prototype.exe_name != None)
#		exe_name = n.prototype.exe_name
		expr = n.prototype.exe_name + "(" + string.join(args + outs, ", ") + ")"

#	expr = exe_name + "(" + string.join(args, ", ") + string.join(outs, ", ") + ")"
	is_expr = len(outputs) == 1 and len(outputs[0][2]) == 1

#	print "\texpr:", expr, "is_expr:", is_expr

	if is_expr :
		((out_term, out_t_nr, succs), ) = outputs
		subtrees[succs[0]] = expr
		assert(len(outputs)==1 and len(outputs[0][2])==1)
		subtrees[outputs[0][2][0]] = expr
	else :
		if len(outputs) == 0 :
			code.append(expr + ";")
		elif len(outputs) == 1 :
			code.append("tmp%i = %s;" % (slot, expr))
		else :
			code.append(expr + ";")

# ------------------------------------------------------------------------------------------------------------

def codegen_alt(g, expd_dels, meta) :

	tmp = temp_init()
	subtrees = {}
	code = []
	dft_alt(g, post_visit = partial(__post_visit, g, code, tmp, subtrees, expd_dels))

	assert(tmp_used_slots(tmp) == 0)
	assert(len(subtrees) == 0)

	variables = ([ "del%i = %i" % (i, int(d.value))
			for d, i in zip(sorted(expd_dels.keys(), lambda x,y: y.nr-x.nr), count()) ] +
		     [ "tmp%i" % i for i in range(len(tmp)) ] +
		     [ "dummy" ])

	output = ("void tsk()" + linesep + "{" + linesep +
		# locals and delays
		(("\tvm_word_t " + string.join(variables, ", ") + ";" + linesep)
			if len(variables) else "") +
		# main loop
		"\tfor(;;)"+ linesep + "\t{" + linesep +
		"\t\t" + string.join(code, linesep + "\t\t") + linesep +
		"\t}" + linesep +
		linesep + "}")
	return output

# ------------------------------------------------------------------------------------------------------------


