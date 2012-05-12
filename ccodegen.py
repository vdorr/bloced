
import core
from os import linesep
from functools import partial
from itertools import count
from pprint import pprint
from itertools import groupby
from implement import block_value_by_name, add_tmp_ref, pop_tmp_ref, \
	temp_init, dft_alt, tmp_used_slots, parse_literal, tmp_max_slots_used, get_terms_flattened
from utils import here

# ------------------------------------------------------------------------------------------------------------

#TODO argument number checking
__OPS = {
	"xor" :		lambda n, args : "(" + "!=".join(("!" + a) for a in args) + ")",
	"or" :		lambda n, args : "(" + "||".join(args) + ")",
	"nor" :		lambda n, args : "!(" + "||".join(args) + ")",
	"and" :		lambda n, args : "(" + "&&".join(args) + ")",
	"nand" :	lambda n, args : "!(" + "&&".join(args) + ")",
	"not" :		lambda n, arg : "!(" + arg[0] + ")",

	"bwxor" :	lambda n, args : "(" + "^".join(args) + ")",
	"bwor" :	lambda n, args : "(" + "|".join(args) + ")",
	"bwnor" :	lambda n, args : "!(" + "|".join(args) + ")",
	"bwand" :	lambda n, args : "(" + "&".join(args) + ")",
	"bwnand" :	lambda n, args : "!(" + "&".join(args) + ")",
	"bwnot" :	lambda n, arg : "~({0}".format(arg[0]),
	"lsl" :		lambda n, arg : "({0}<<{1})".format(arg[0], arg[1]),
	"lsr" :		lambda n, arg : "({0}>>{1})".format(arg[0], arg[1]),

	"add" :		lambda n, args : "(" + "+".join(args) + ")",
	"sub" :		lambda n, args : "(" + "-".join(args) + ")",
	"mul" :		lambda n, args : "(" + "*".join(args) + ")",
	"div" :		lambda n, args : "(" + "/".join(args) + ")",
	"mod" :		lambda n, args : "(" + "%".join(args) + ")",
	"abs" :		lambda n, args : "(({0}<0)?(-{0}):({0}))".format(args[0]),
	"lt" :		lambda n, args : "(" + "<".join(args) + ")",
	"gt" :		lambda n, args : "(" + ">".join(args) + ")",
	"lte" :		lambda n, args : "(" + "<=".join(args) + ")",
	"gte" :		lambda n, args : "(" + ">=".join(args) + ")",
	"eq" :		lambda n, args : "(" + "==".join(args) + ")",
	#"divmod"
}

def __arg_zipper(term_pairs, arguments) :
	i = 0
	for t, t_nr in term_pairs :
#		print here(), t, t_nr, i
		if t_nr is None :
			yield (t, t_nr), None
		else :
			if i < len(arguments) :
				yield (t, t_nr), arguments[i] 
				i += 1
			else :
				yield (t, t_nr), None


def __arg_grouper(term_pairs, arguments) :
	return  groupby(tuple(__arg_zipper(term_pairs, arguments)), key=lambda i: (i[0][0].name, i[0][0].variadic))


def __make_call(n, args, outs, tmp_var_args, code) :

	assert(n.prototype.exe_name != None)

	tmp_args = { type_name : None for type_name in core.KNOWN_TYPES }
#	inputs = in_terms(n)
#	outputs = out_terms(n)

	inputs = tuple(get_terms_flattened(n, direction=core.INPUT_TERM,
		fill_for_unconnected_var_terms=True))
	outputs = tuple(get_terms_flattened(n, direction=core.OUTPUT_TERM,
		fill_for_unconnected_var_terms=True))

#	assert(len(args)==len(inputs))
#	assert((len(outs)==len(outputs)) or (len(outs)==0 and len(outputs)==1) and not outputs[0][0].variadic)

	arg_list = []

	for term_pairs, arguments in ((inputs, args), (outputs, outs)) :
		for (name, variadic), arg_group_it in __arg_grouper(term_pairs, arguments) :
			if variadic :
				arg_group = tuple((t, a) for (t, t_nr), a in arg_group_it if not t_nr is None)
				if not arg_group :
					arg_code = "NULL"
				else :
					arg_type = arg_group[0][0].type_name
					assert(all(t.type_name == arg_type for t, _ in arg_group))
					array_size = tmp_args[arg_type]
					array_size = 0 if array_size is None else array_size
					code.extend("{0}_tmp_arg[{1}]={2}".format(arg_type, array_size+i, a)
						for (_, a), i in zip(arg_group, count()))
					tmp_args[arg_type] = array_size + len(arg_group)
					arg_code = "&{0}_tmp_arg[{1}]".format(arg_type, len(arg_group))
				arg_list.append(str(len(arg_group)))
				arg_list.append(arg_code)
			else :
				((t, t_nr), a), = arg_group_it
				assert((len(outputs)==1 and not t.variadic) if a is None else True);
				if not a is None :
					arg_list.append(a)

	for type_name, cnt in tmp_args.items() :
		array_size = tmp_var_args[type_name]
		if not cnt is None and (array_size is None or (array_size+cnt) > array_size) :
#			print here(), type_name, cnt
			tmp_var_args[type_name] = cnt

	return n.prototype.exe_name + "(" + ", ".join(arg_list) + ")"


def __implement(g, n, tmp_args, args, outs, code) :
#, types, known_types, pipe_vars) :
#	print here(2), n, args, outs
#	print(here(), n.prototype.type_name, n.prototype.library)
	if n.prototype.type_name in __OPS :
		assert(len(args) >= 2 or n.prototype.type_name in ("not", "abs"))
		assert(len([t for t in n.terms if t.direction==core.OUTPUT_TERM]) == 1)
		return __OPS[n.prototype.type_name](n, tuple("({0})".format(a) for a in args))
	elif core.compare_proto_to_type(n.prototype, core.FunctionCallProto) :
		func_name = block_value_by_name(n, "Name")
		assert(func_name)
		return func_name + "(" + ", ".join(args + outs) + ")"
	elif core.compare_proto_to_type(n.prototype, core.GlobalReadProto) :
		assert(len(args)==0)
		pipe_name = block_value_by_name(n, "Name")
		assert(pipe_name)
		return pipe_name
	elif core.compare_proto_to_type(n.prototype, core.GlobalWriteProto) :
		assert(len(args)==1)
		pipe_name = block_value_by_name(n, "Name")
		assert(pipe_name)
		return "{0} = {1}".format(pipe_name, args[0])
	elif core.compare_proto_to_type(n.prototype, core.MuxProto) :
		assert(len(args)==3)
		return "({0} ? {2} : {1})".format(*args)#XXX cast sometimes needed!!!
	elif core.compare_proto_to_type(n.prototype, core.TypecastProto) :
		assert(len(args)==1)
		out = tuple(t for t in n.terms if t.direction==core.OUTPUT_TERM)
		assert(len(out)==1)
		return "({0})({1})".format(out[0].type_name, args[0])
	else :
		return __make_call(n, args, outs, tmp_args, code)
#		assert(n.prototype.exe_name != None)
#		return n.prototype.exe_name + "(" + ", ".join(args + outs) + ")"


def __post_visit(g, code, tmp, tmp_args, subtrees, expd_dels, types, known_types,
		dummies, state_var_prefix, pipe_vars, libs_used, evaluated, n, visited) :
#	print "__post_visit:", n.to_string()

	if core.compare_proto_to_type(n.prototype, core.ConstProto) :
		return None # handled elsewhere

	if n.prototype.library :
		libs_used.add(n.prototype.library)

	inputs_all, outputs_all = g[n]
	inputs = [ (t, nr, ngh) for t, nr, ngh in inputs_all if not t.virtual ]
	outputs = [ (t, nr, ngh) for t, nr, ngh in outputs_all if not t.virtual ]

	args = []
	outs = []

#	print here(), n, tmp, subtrees
#	print here(), n, outputs

	for out_term, out_t_nr, succs in outputs :
#		if out_term.virtual :
#			continue
		if out_term.type_name == core.TYPE_INFERRED :
			term_type = types[n, out_term, out_t_nr]
		else :
			term_type = out_term.type_name
#		print "out_term, out_t_nr, succs =", n, out_term, out_term.type_name, out_t_nr, succs
		if len(succs) > 1 or (len(outputs) > 1 and len(succs) == 1):
#			print "adding temps:", succs
			expr_slot_type = term_type
			expr_slot = add_tmp_ref(tmp, succs, slot_type=term_type)
#TODO if all succs have same type different from out_term, cast now and store as new type
#if storage permits, however
			if len(outputs) > 1 :
				outs.append("&{0}_tmp{1}".format(expr_slot_type, expr_slot))
		elif len(succs) == 1 and len(outputs) == 1 :
#			print here(), "passing by", n
			pass
		else :
			dummies.add(term_type)
			outs.append("&"+term_type+"_dummy")

	for in_term, in_t_nr, preds in inputs :
#		print here(), n, preds
		assert(len(preds)==1)

#		if out_term.virtual :
#			continue

		((m, m_t, m_t_nr), ) = preds
#		print "\tgathering:", m, m_t, m_t_nr, "for", (n, in_term, in_t_nr), "subtrees:", subtrees, "tmp:", tmp
		if core.compare_proto_to_type(m.prototype, core.ConstProto) :
			assert(m.value != None)
			assert(len(m.value) == 1)
			args.append(str(m.value[0]))
		elif (n, in_term, in_t_nr) in subtrees :
			args.append(subtrees.pop((n, in_term, in_t_nr)))
		else :
			slot_type, slot = pop_tmp_ref(tmp, n, in_term, in_t_nr)
			if slot != None:
				args.append("{0}_tmp{1}".format(slot_type, slot))
			else :
#				print subtrees.keys()[0][0], subtrees.keys()[0][1], id(subtrees.keys()[0][0]), id(subtrees.keys()[0][1])
				raise Exception("holy shit! %s not found, %s %s" %
					(str((id(n), id(in_term), in_t_nr)), str(tmp), str(subtrees)))

	if core.compare_proto_to_type(n.prototype, core.DelayInProto) :
		del_in, del_out = expd_dels[n.delay]
		assert(n==del_in)
		if not del_out in evaluated :
#			print(here(), del_out.type_name)
			slot = add_tmp_ref(tmp, [ (del_in, del_in.terms[0], 0) ],
				slot_type=del_out.type_name)#XXX typed signal XXX with inferred type!!!!!
			code.append("{0}_tmp{1} = {2}del{3}".format(del_out.type_name, slot, state_var_prefix, n.nr))
#		print here(), del_out
		expr = "{0}del{1}={2}".format(state_var_prefix, n.nr, args[0])
	elif core.compare_proto_to_type(n.prototype, core.DelayOutProto) :
		del_in, del_out = expd_dels[n.delay]
		assert(n==del_out)
#		print(here(), "del_in=", del_in, n.delay, visited.keys())
		if del_in in evaluated : #visited :
			slot_type, slot = pop_tmp_ref(tmp, del_in, del_in.terms[0], 0)
			expr = "{0}_tmp{1}".format(slot_type, slot)
		else :
			expr = "{0}del{1}".format(state_var_prefix, n.nr)
	else :
#		print(here(), n.prototype.type_name)
		expr = __implement(g, n, tmp_args, args, outs, code)#, types, known_types, pipe_vars)

	is_expr = len(outputs) == 1 and len(outputs[0][2]) == 1
#	print "\texpr:", expr, "is_expr:", is_expr#, "tmp=", tmp

	if is_expr :
		((out_term, out_t_nr, succs), ) = outputs
		subtrees[succs[0]] = expr
		assert(len(outputs)==1 and len(outputs[0][2])==1)
		subtrees[outputs[0][2][0]] = expr
	else :
		if len(outputs) == 0 :
			code.append(expr + ";")
		elif len(outputs) == 1 :
#			(out_term,) = [ trm for trm in n.terms if trm.direction == core.OUTPUT_TERM ]
#			term_type = types[ n, out_term, 0 ]
#			slot = add_tmp_ref(tmp, outputs[0][2], slot_type=term_type)
#			print here(), n, out_term, term_type, "slot=", slot
#			pprint(tmp)

			code.append("{0}_tmp{1} = {2};".format(expr_slot_type, expr_slot, expr))
		else :
			code.append(expr + ";")

	evaluated[n] = True


# ------------------------------------------------------------------------------------------------------------

#def codegen_alt(g, expd_dels, meta, types, known_types, pipe_vars, libs_used, task_name="tsk") :
#	tsk_name, cg_out = codegen(g, expd_dels, meta, types, known_types, pipe_vars, libs_used, task_name=task_name)
#	return churn_task_code(tsk_name, cg_out)


def codegen(g, expd_dels, meta, types, known_types, pipe_vars, libs_used, task_name = "tsk") :

	tmp = temp_init(known_types)
	subtrees = {}
	code = []
	dummies = set()
	state_var_prefix = task_name + "_"
	evaluated = {}
	tmp_args = { type_name : None for type_name in core.KNOWN_TYPES }

	post_visit_callback = partial(__post_visit, g, code, tmp, tmp_args, subtrees,
		expd_dels, types, known_types, dummies, state_var_prefix, pipe_vars, libs_used, evaluated)

#	pprint(g)
	dft_alt(g, post_visit=post_visit_callback)

#	pprint(tmp)

	assert(tmp_used_slots(tmp) == 0)
	assert(len(subtrees) == 0)

	return task_name, (code, types, tmp, tmp_args, expd_dels, pipe_vars, dummies, meta, known_types)


def churn_task_code(task_name, cg_out) :
#TODO list known meta values

	code, types, tmp, tmp_args, expd_dels, global_vars, dummies, meta, known_types = cg_out

	state_var_prefix = task_name + "_"
	state_vars = []
#	print(dir(expd_dels.keys()[0]))
	for d, i in zip(sorted(expd_dels.keys(), key=lambda x: expd_dels[x][0].nr), count()) :
#	for d, i in zip(sorted(expd_dels.keys(), lambda x,y: y.nr-x.nr), count()) :
		del_out = expd_dels[d][1]
		del_type = types[del_out, del_out.terms[0], 0]
		_, del_init = parse_literal(d.value[0], known_types=known_types, variables={})
		state_vars.append("\t{0} {1}del{2} = {3};{4}".format(
			del_type, state_var_prefix, i, del_init, linesep))

	temp_vars = []
	for slot_type in sorted(tmp.keys()) :
		slot_cnt = tmp_max_slots_used(tmp, slot_type=slot_type)
		if slot_cnt > 0 :
			names = [ "{0}_tmp{1}".format(slot_type, i) for i in range(slot_cnt) ]
			temp_vars.append("\t" + slot_type + " " + ", ".join(names) + ";" + linesep)

	for slot_type, array_size in sorted(tmp_args.items(), key=lambda item: item[0]) :
		if not array_size is None :
			temp_vars.append("\t{0} {0}_tmp_arg[{1}];{2}".format(slot_type, array_size, linesep))

	dummy_vars = [ "\t{0} {0}_dummy;{1}".format(tp, linesep) for tp in dummies ]

	if "function_wrap" in meta and not meta["function_wrap"] :
		pass #TODO
	else :
		pass #TODO

	if "endless_loop_wrap" in meta and not meta["endless_loop_wrap"] :
		loop_code = "\t" + (linesep + "\t").join(code)
	else :
		loop_code = linesep.join(("\tfor(;;)", "\t{", "\t\t" + (linesep + "\t\t").join(code), "\t}"))

	decl = "void " + task_name + "()"

	output = (decl + linesep + "{" + linesep +
		# locals and delays
		"".join(temp_vars + state_vars + dummy_vars) +
		# main loop
		loop_code + linesep +
		"}")

	return decl + ";", output


def churn_code(meta, global_vars, tsk_cg_out, include_files, f) :
	"""
	tasks_cg_out = [ (task_name, cg_out), ... ]
	f - writeble filelike object
	"""

	f.write("".join('#include "{0}"{1}'.format(incl, linesep) for incl in include_files))

	decls = []
	functions = []
#	for name, cg_out in sorted(tsk_cg_out.items(), key=lambda x: x[0]) :
	for name, cg_out in tsk_cg_out :
		decl, func = churn_task_code(name, cg_out)
		decls.append(decl)
		decls.append(linesep)
		functions.append(func)

	f.write("".join(decls))

	g_vars_grouped = groupby(sorted(global_vars, key=lambda x: x[1]), key=lambda x: x[1])
	g_vars_code = tuple((pipe_type + " " + ",".join(
		(i+" = "+str(pipe_default)for (i, _, pipe_default) in sorted(vlist))) + ";" + linesep)
			for pipe_type, vlist in g_vars_grouped)

#	pprint(g_vars_code)
#	print here(), g_vars_code
	f.write(linesep.join(g_vars_code))

	f.write(linesep.join(functions))




