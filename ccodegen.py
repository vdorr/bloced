
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

__operators = {
	"xor" :		lambda n, args : "(" + string.join(args, "^") + ")",
	"or" :		lambda n, args : "(" + string.join(args, "|") + ")",
	"nor" :		lambda n, args : "!(" + string.join(args, "|") + ")",
	"and" :		lambda n, args : "(" + string.join(args, "&") + ")",
	"nand" :	lambda n, args : "!(" + string.join(args, "&") + ")",
	"not" :		lambda n, (arg,) : "!(" + arg + ")",
	"add" :		lambda n, args : "(" + string.join(args, "+") + ")",
	"sub" :		lambda n, args : "(" + string.join(args, "-") + ")",
	"mul" :		lambda n, args : "(" + string.join(args, "*") + ")",
	"div" :		lambda n, args : "(" + string.join(args, "/") + ")",
	"mod" :		lambda n, args : "(" + string.join(args, "%") + ")",
	#"divmod"
}

def __implement(n, args, outs) :
	if n.prototype.type_name in __operators :
		assert(len(args) >= 2)
		assert(len(outs) == 1)
		return __operators[n.prototype.type_name](n, args)
	else :
		return n.prototype.exe_name + "(" + string.join(args + outs, ", ") + ")"

# execution
def __post_visit(g, code, tmp, subtrees, expd_dels, n, visited) :

#TODO can i get rid off som cycles by use of other callbacks?

	if isinstance(n.prototype, core.ConstProto) :
		return None # handled elsewhere

	inputs, outputs = g[n]

	args = []
	outs = []#TODO TODO TODO

#	print "__post_visit:", n, tmp, subtrees

	for out_term, out_t_nr, succs in outputs :
		print "out_term, out_t_nr, succs =", n, out_term, out_t_nr, succs
		if len(succs) > 1 or (len(outputs) > 1 and len(succs) == 1):
#			print "adding temps:", succs
			slot = add_tmp_ref(tmp, succs)
			outs.append("&tmp%i"%slot)
		elif len(succs) == 1 and len(outputs) == 1 :
			pass
		else :
			outs.append("&dummy")

	#gather inputs
	for in_term, in_t_nr, preds in inputs :
		assert(len(preds)==1)
		((m, m_t, m_t_nr), ) = preds
#		print "\tgathering:", m, m_t, m_t_nr, "for", (n, in_term, in_t_nr), "subtrees:", subtrees, "tmp:", tmp
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
				raise Exception("holy shit! %s not found, %s %s" %
					(str((n, in_term, in_t_nr)), str(tmp), str(subtrees)))

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
		expr = __implement(n, args, outs)
#		expr = n.prototype.exe_name + "(" + string.join(args + outs, ", ") + ")"

#	expr = exe_name + "(" + string.join(args, ", ") + string.join(outs, ", ") + ")"
	is_expr = len(outputs) == 1 and len(outputs[0][2]) == 1

#	print "\texpr:", expr, "is_expr:", is_expr, "tmp=", tmp

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

def generate(g, expd_dels) :
	tmp = temp_init()
	subtrees = {}
	code = []
	dft_alt(g, post_visit = partial(__post_visit, g, code, tmp, subtrees, expd_dels))
	assert(tmp_used_slots(tmp) == 0)
	assert(len(subtrees) == 0)

	state_var_prefix = ""
	state_vars = [ "%sdel%i = %i" % (state_var_prefix, i, int(d.value))
			for d, i in zip(sorted(expd_dels.keys(), lambda x,y: y.nr-x.nr), count()) ]

	temp_var_prefix = ""
	temp_vars = [ "%stmp%i" % (temp_var_prefix, i) for i in range(len(tmp)) ] + [ "dummy" ]

	return (state_vars, temp_vars, code)

# ------------------------------------------------------------------------------------------------------------

def codegen_alt(g, expd_dels, meta) :
#		function_name="tsk",
#		separate_state_vars=False,
#		separate_temp_vars=False,
##		shared_temp_vars=False,
#		wrap_in_function=True,
#		wrap_in_loop=True,
#		infer_signature=True,
#		input_blocks=None,
#		output_blocks=None) :
#	pprint(g)
	tmp = temp_init()
	subtrees = {}
	code = []
	dft_alt(g, post_visit = partial(__post_visit, g, code, tmp, subtrees, expd_dels))
#	print tmp
	assert(tmp_used_slots(tmp) == 0)
	assert(len(subtrees) == 0)

#TODO get name of task from from meta
#TODO return state variables separately from task code
#TODO mangle state vars names so that state vars from different task can share the same namespace
#TODO infer function prototype from Input/Output blocks

	state_var_prefix = ""
	state_vars = [ "%sdel%i = %i" % (state_var_prefix, i, int(d.value))
			for d, i in zip(sorted(expd_dels.keys(), lambda x,y: y.nr-x.nr), count()) ]

	temp_var_prefix = ""
	temp_vars = [ "%stmp%i" % (temp_var_prefix, i) for i in range(len(tmp)) ] + [ "dummy" ]

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


