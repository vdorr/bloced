
import dfs
from dfs import INPUT_TERM, OUTPUT_TERM
import core
from os import linesep
from functools import partial
from itertools import count
from pprint import pprint
from implement import *

# ------------------------------------------------------------------------------------------------------------

__operators = {
	"xor" :		lambda n, args : "(" + "^".join(args) + ")",
	"or" :		lambda n, args : "(" + "|".join(args) + ")",
	"nor" :		lambda n, args : "!(" + "|".join(args) + ")",
	"and" :		lambda n, args : "(" + "&".join(args) + ")",
	"nand" :	lambda n, args : "!(" + "&".join(args) + ")",
	"not" :		lambda n, arg : "!(" + arg[0] + ")",
	"add" :		lambda n, args : "(" + "+".join(args) + ")",
	"sub" :		lambda n, args : "(" + "-".join(args) + ")",
	"mul" :		lambda n, args : "(" + "*".join(args) + ")",
	"div" :		lambda n, args : "(" + "/".join(args) + ")",
	"mod" :		lambda n, args : "(" + "%".join(args) + ")",
	"lt" :		lambda n, args : "(" + "<".join(args) + ")",
	"gt" :		lambda n, args : "(" + ">".join(args) + ")",
	"lte" :		lambda n, args : "(" + "<=".join(args) + ")",
	"gte" :		lambda n, args : "(" + ">=".join(args) + ")",
	"eq" :		lambda n, args : "(" + "==".join(args) + ")",
	#"divmod"
}


def __implement(n, args, outs, pipe_vars) :
#	print here(2), n, args, outs
#	print(here(), n.prototype.type_name)
	if n.prototype.type_name in __operators :
		assert(len(args) >= 2)
		assert(len([t for t in n.terms if t.direction==OUTPUT_TERM]) == 1)
		return __operators[n.prototype.type_name](n, args)
	elif n.prototype.__class__ == core.PipeProto :
		assert(len(args) == 1)
		assert(not outs)
		pipe_name = block_value_by_name(n, "Name")
		assert(not pipe_name in pipe_vars)
		i, = max(pipe_vars.values(), key=lambda x: x[0]) if pipe_vars else (0, )
		pipe_vars[pipe_name] = (i + 1, )
		return "global{0} = {1}".format(i + 1, args[0])
	elif n.prototype.__class__ == core.PipeEndProto :
		pipe_name = block_value_by_name(n, "Name")
		return "global{0}".format(pipe_vars[pipe_name])
	else :
		assert(n.prototype.exe_name != None)
		return n.prototype.exe_name + "(" + ", ".join(args + outs) + ")"


def __post_visit(g, code, tmp, subtrees, expd_dels, types, dummies, state_var_prefix, pipe_vars, n, visited) :
#	print "__post_visit:", n.to_string()

	if isinstance(n.prototype, core.ConstProto) :
		return None # handled elsewhere

	inputs, outputs = g[n]

	args = []
	outs = []

#	print "__post_visit:", n, tmp, subtrees
#	print here(), n, outputs

	for out_term, out_t_nr, succs in outputs :
		if out_term.type_name == "<inferred>" :
			if n.prototype.__class__ == core.PipeEndProto :
				pipe_name = block_value_by_name(n, "Name")
				pipe_index, pipe_type = pipe_vars[pipe_name]
				term_type = pipe_type
			else :
				term_type = types[n, out_term, out_t_nr]
		else :
			term_type = out_term.type_name
#		print "out_term, out_t_nr, succs =", n, out_term, out_term.type_name, out_t_nr, succs
		if len(succs) > 1 or (len(outputs) > 1 and len(succs) == 1):
#			print "adding temps:", succs
			slot = add_tmp_ref(tmp, succs,
				slot_type=term_type)
#TODO if all succs have same type different from out_term, cast now and store as new type
#if storage permits, however
			outs.append("&tmp%i"%slot)
		elif len(succs) == 1 and len(outputs) == 1 :
#			print "passing by"
			pass
		else :
			dummies.add(term_type)
			outs.append("&"+term_type+"_dummy")

	for in_term, in_t_nr, preds in inputs :
		assert(len(preds)==1)
		((m, m_t, m_t_nr), ) = preds
#		print "\tgathering:", m, m_t, m_t_nr, "for", (n, in_term, in_t_nr), "subtrees:", subtrees, "tmp:", tmp
		if isinstance(m.prototype, core.ConstProto) :
			assert(m.value != None)
			assert(len(m.value) == 1)
			args.append(str(m.value[0]))
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
		assert(n==del_in)
		if not del_out in visited :
#			print here(), del_out.type_name
			slot = add_tmp_ref(tmp, [ (del_in, del_in.terms[0], 0) ],
				slot_type=del_out.type_name)#XXX typed signal XXX with inferred type!!!!!
			code.append("tmp{0} = {1}del{2}".format(slot, state_var_prefix, n.nr))
		expr = "{0}del{1}={2}".format(state_var_prefix, n.nr, args[0])
	elif isinstance(n.prototype, core.DelayOutProto) :
		del_in, del_out = expd_dels[n.delay]
		assert(n==del_out)
#		print "\tdel_in=", del_in, n.delay
		if del_in in visited :
			slot = pop_tmp_ref(tmp, del_in, del_in.terms[0], 0)
			expr = "tmp%i" % slot
		else :
			expr = "{0}del{1}".format(state_var_prefix, n.nr)
#	elif n.prototype.__class__ == core.PipeProto :
#		print(here(), )
#		slot = add_tmp_ref(global_vars, [], slot_type="vm_word_t")
#		code.append("global{0} = {1}del{2}".format(slot, state_var_prefix, n.nr))

#	elif n.prototype.__class__ == core.PipeEndProto :
#		print(here(), )
##		slot = add_tmp_ref(global_vars, refs, slot_type="vm_word_t") 
	else :
		print(here(), n.prototype.type_name)
		expr = __implement(n, args, outs, pipe_vars)

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

def codegen_alt(g, expd_dels, meta, types, task_name="tsk") :
	tsk_name, cg_out = codegen(g, expd_dels, meta, types, task_name=task_name)
	return churn_code(tsk_name, meta, cg_out)


def codegen(g, expd_dels, meta, types, task_name = "tsk") :

	tmp = temp_init(core.KNOWN_TYPES)
	subtrees = {}
	code = []
	dummies = set()
	state_var_prefix = task_name + "_"

#	global_vars = temp_init(core.KNOWN_TYPES)

	pipes = [ (n, (p, s)) for n, (p, s) in g.items() if n.prototype.__class__ == core.PipeProto ]
	pipe_ends = [ (n, (p, s)) for n, (p, s) in g.items() if n.prototype.__class__ == core.PipeEndProto ]

	pipe_vars = {}

#	for n, (p, s) in pipes :




#	pipe_index = {}

#	for n, (p, s) in pipe_ends :
#		assert(not p)
#		pipe_name = block_value_by_name(n, "Name")
##		pipe_index[pipe_name]

#		slot_type #based on pipe default value and pipe preds

#		slot = add_tmp_ref(global_vars, s, slot_type=slot_type) 

#block_value_by_name(n, "Name")

#	add_tmp_ref(global_vars, refs, slot_type="vm_word_t") 




	post_visit_callback = partial(__post_visit, g, code, tmp, subtrees,
		expd_dels, types, dummies, state_var_prefix, pipe_vars)

	dft_alt(g, post_visit=post_visit_callback)

	assert(tmp_used_slots(tmp) == 0)
	assert(len(subtrees) == 0)

	return task_name, (code, types, tmp, expd_dels, pipe_vars, dummies)


def merge_codegen_output(a, b) :

	code0, types0, tmp0, expd_dels0, global_vars0, dummies0 = a
	code1, types1, tmp1, expd_dels1, global_vars1, dummies1 = b

	code = code0 + code1

	types = dict(types0)
	types.update(types1)

	tmp = tmp_merge(tmp0, tmp1)

	expd_dels = dict(expd_dels0)
	expd_dels.update(expd_dels1)

	dummies = dummies0.union(dummies1)

	global_vars = None#TODO

	return code, types, tmp, expd_dels, global_vars, dummies


def churn_code(task_name, meta, cg_out) :
	code, types, tmp, expd_dels, global_vars, dummies = cg_out

	state_var_prefix = task_name + "_"
	state_vars = []
#	print(dir(expd_dels.keys()[0]))
	for d, i in zip(sorted(expd_dels.keys(), key=lambda x: expd_dels[x][0].nr), count()) :
#	for d, i in zip(sorted(expd_dels.keys(), lambda x,y: y.nr-x.nr), count()) :
		del_in = expd_dels[d][0]
		del_type = types[del_in, del_in.terms[0], 0]
		state_vars.append("\t{0} {1}del{2} = {3};{4}".format(
			del_type, state_var_prefix, i, int(d.value[0]), linesep))

	temp_vars = []
	for slot_type in sorted(tmp.keys()) :
		slot_cnt = tmp_max_slots_used(tmp, slot_type=slot_type)
		if slot_cnt > 0 :
			names = [ "tmp{0}".format(i) for i in range(slot_cnt) ]
			temp_vars.append("\t" + slot_type + " " + ", ".join(names) + ";" + linesep)

	dummy_vars = [ "\t{0} {0}_dummy;{1}".format(tp, linesep) for tp in dummies ]

	if "endless_loop_wrap" in meta and not meta["endless_loop_wrap"] :
		loop_code = "\t" + (linesep + "\t\t").join(code)
	else :
		loop_code = linesep.join(("\tfor(;;)", "\t{", "\t\t" + (linesep + "\t\t").join(code), "\t}"))

	output = ("void " + task_name + "()" + linesep + "{" + linesep +
		# locals and delays
		"".join(temp_vars + state_vars + dummy_vars) +
		# main loop
		loop_code + linesep +
		"}")

	return output

# ------------------------------------------------------------------------------------------------------------


