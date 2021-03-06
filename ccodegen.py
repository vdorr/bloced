
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

#TODO argument number and type checking
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
		if t_nr is None :
			yield (t, t_nr), None
		else :
			if i < len(arguments) :
				yield (t, t_nr), arguments[t, t_nr]# , arguments[i] 
				i += 1
			else :
				yield (t, t_nr), None


def __arg_grouper(term_pairs, arguments) :
	return  groupby(tuple(__arg_zipper(term_pairs, arguments)),
		key=lambda i: (i[0][0].name, i[0][0].variadic))


def __make_call(n, args_and_terms, outs_and_terms, tmp_var_args, code) :
	"""
	generate code for function call
	"""

	assert(not n.prototype.exe_name is None)

	tmp_args = { type_name : None for type_name in core.KNOWN_TYPES }

	arg_list = []

	arguments = dict(args_and_terms + outs_and_terms)
	term_pairs = get_terms_flattened(n, fill_for_unconnected_var_terms=True)
	args_grouped = __arg_grouper(term_pairs, arguments)

	outputs_cnt = sum((1 for _ in get_terms_flattened(n, direction=core.OUTPUT_TERM,
		fill_for_unconnected_var_terms=True)))

	for (_, variadic), arg_group_it in args_grouped :
		if variadic :
			arg_group = tuple((t, a) for (t, t_nr), a in arg_group_it if not t_nr is None)
			if not arg_group :
				arg_code = "NULL"
			else :
				arg_type = arg_group[0][0].type_name
				assert(all(t.type_name == arg_type for t, _ in arg_group))
				array_size = tmp_args[arg_type]
				array_size = 0 if array_size is None else array_size
				code.extend("{0}_tmp_arg[{1}]={2};".format(arg_type, array_size+i, a)
					for (_, a), i in zip(arg_group, count()))
				tmp_args[arg_type] = array_size + len(arg_group)
				arg_code = "&{0}_tmp_arg[{1}]".format(arg_type, array_size)
			arg_list.append(str(len(arg_group)))
			arg_list.append(arg_code)
		else :
			((t, _), a), = arg_group_it
#			print here(), term_pairs, outputs_cnt
			assert((outputs_cnt==1 and not t.variadic) if a is None else True)
			if not a is None :
				arg_list.append(a)

	for type_name, cnt in tmp_args.items() :
		array_size = tmp_var_args[type_name]
		if not cnt is None and (array_size is None or (array_size+cnt) > array_size) :
			tmp_var_args[type_name] = cnt

	return n.prototype.exe_name + "(" + ", ".join(arg_list) + ")"


def __implement(g, n, tmp_args, args, outs, code) :
	"""
	return code to perform block n
	"""
	stmt = None
	if n.prototype.type_name in __OPS :
		assert(len(args) >= 2 or n.prototype.type_name in ("not", "abs"))
		assert(len([t for t in n.terms if t.direction==core.OUTPUT_TERM]) == 1)
		stmt = __OPS[n.prototype.type_name](n, tuple("({0})".format(a) for _, a in args))
	elif core.compare_proto_to_type(n.prototype, core.FunctionCallProto) :
		func_name = block_value_by_name(n, "Name")
		assert(func_name)
		stmt = func_name + "(" + ", ".join(tuple(a for _, a in (args + outs))) + ")"
	elif core.compare_proto_to_type(n.prototype, core.GlobalReadProto) :
		assert(len(args)==0)
		pipe_name = block_value_by_name(n, "Name")
		assert(pipe_name)
		stmt = pipe_name
	elif core.compare_proto_to_type(n.prototype, core.GlobalWriteProto) :
		assert(len(args)==1)
		pipe_name = block_value_by_name(n, "Name")
		assert(pipe_name)
		stmt = "{0} = {1}".format(pipe_name, args[0][1])
	elif core.compare_proto_to_type(n.prototype, core.MuxProto) :
		assert(len(args)==3)
		stmt = "({0} ? {2} : {1})".format(*tuple(a for _, a in args))#XXX cast sometimes needed!!!
	elif core.compare_proto_to_type(n.prototype, core.TypecastProto) :
		assert(len(args)==1)
		out = tuple(t for t in n.terms if t.direction==core.OUTPUT_TERM)
		assert(len(out)==1)
		stmt = "({0})({1})".format(out[0].type_name, args[0][1])
	else :
		stmt = __make_call(n, args, outs, tmp_args, code)
#		assert(n.prototype.exe_name != None)
#		return n.prototype.exe_name + "(" + ", ".join(args + outs) + ")"
	assert(not stmt is None)
	return stmt


def __get_initdel_value(code, n, state_var_prefix, del_type, tmp_slot, expr) :
	"""
	generate code for InitDelay block
	"""
	code.append("if ( {0}del{1}_init ) {{".format(state_var_prefix, n.nr))
	code.append("{0}_tmp{1} = {2}del{3};".format(del_type, tmp_slot, state_var_prefix, n.nr))
	code.append("} else {")
	code.append("{0}del{1}_init = 1;".format(state_var_prefix, n.nr))
	code.append("{0}_tmp{1} = {2};".format(del_type, tmp_slot, expr))
	code.append("}")


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

	expr_slot_type = None

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
				outs.append(((out_term, out_t_nr), "&{}_tmp{}".format(expr_slot_type, expr_slot)))
		elif len(succs) == 1 and len(outputs) == 1 :
#			print here(), "passing by", n
			pass
		else :
			dummies.add(term_type)
			outs.append(((out_term, out_t_nr), "&{}_dummy".format(term_type)))

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
			args.append(((in_term, in_t_nr), str(m.value[0])))
		elif (n, in_term, in_t_nr) in subtrees :
			args.append(((in_term, in_t_nr), subtrees.pop((n, in_term, in_t_nr))))
		else :
			slot_type, slot = pop_tmp_ref(tmp, n, in_term, in_t_nr)
			if slot != None:
				args.append(((in_term, in_t_nr), "{0}_tmp{1}".format(slot_type, slot)))
			else :
				assert(False)

	if core.compare_proto_to_type(n.prototype, core.DelayInProto) :
		del_in, del_out = expd_dels[n.delay]
		assert(n==del_in)
#		is_initdel = core.compare_proto_to_type(del_out.prototype, core.InitDelayOutProto)
		if not del_out in evaluated :# or is_initdel :
#			print here(), del_in.terms
			del_type = types[del_out, del_out.terms[0], 0]
			slot = add_tmp_ref(tmp, [ (del_in, del_in.terms[0], 0) ], slot_type=del_type)
			if core.compare_proto_to_type(del_out.prototype, core.InitDelayOutProto) :# is_initdel :
#				print here(), args
				assert(len(args)==1 and len(outs)==0)
				__get_initdel_value(code, n, state_var_prefix, del_type, slot, args[0][1])
			else :
				code.append("{0}_tmp{1} = {2}del{3};".format(del_type, slot, state_var_prefix, n.nr))
		expr = "{0}del{1}={2}".format(state_var_prefix, n.nr, args[0][1])

	elif core.compare_proto_to_type(n.prototype, core.DelayOutProto, core.InitDelayOutProto) :
		del_in, del_out = expd_dels[n.delay]
		assert(n==del_out)
		if del_in in evaluated : #visited :
			slot_type, slot = pop_tmp_ref(tmp, del_in, del_in.terms[0], 0)
			expr = "{0}_tmp{1}".format(slot_type, slot)
		else :
			if core.compare_proto_to_type(n.prototype, core.InitDelayOutProto) :
				assert(len(args)==1 and len(outs)==0)
				del_type = types[del_out, del_out.terms[0], 0]
				slot = add_tmp_ref(tmp, [ (del_in, del_in.terms[0], 0) ], slot_type=del_type)
				__get_initdel_value(code, n, state_var_prefix, del_type, slot, args[0][1])
				slot_type, slot = pop_tmp_ref(tmp, del_in, del_in.terms[0], 0)
				expr = "{0}_tmp{1}".format(slot_type, slot)
			else :
				expr = "{0}del{1}".format(state_var_prefix, n.nr)
	else :
		expr = __implement(g, n, tmp_args, args, outs, code)#, types, known_types, pipe_vars)

	is_expr = len(outputs) == 1 and len(outputs[0][2]) == 1

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
			if expr_slot_type is None :
				code.append("(void){};".format(expr))
			else :
				code.append("{0}_tmp{1} = {2};".format(expr_slot_type, expr_slot, expr))
		else :
			code.append(expr + ";")

	evaluated[n] = True


# ------------------------------------------------------------------------------------------------------------


def codegen(g, expd_dels, meta, types, known_types, pipe_vars, libs_used, task_name = "tsk") :
	"""
	generate code and variables for single task
	"""

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

	vars_other = tuple()

	return task_name, (code, types, tmp, tmp_args, expd_dels, pipe_vars, dummies, meta, known_types, vars_other)


def churn_task_code(task_name, cg_out) :
	"""
	from output of function churn code, declarations and variables for single task
	"""
#TODO list known meta values

	code, types, tmp, tmp_args, expd_dels, global_vars, dummies, meta, known_types, vars_other = cg_out

#	meta["endless_loop_wrap"] = False
#	meta["function_attributes"] = "inline"
##	meta["function_prefix"] = "static"
#	meta["state_vars_scope"] = "module"#"local"
#	meta["state_vars_storage"] = "heap"

	endless_loop_wrap = "endless_loop_wrap" in meta and not meta["endless_loop_wrap"]
	function_attributes = meta["function_attributes"] if "function_attributes" in meta else ""#"inline" and such
	function_prefix = meta["function_prefix"] if "function_prefix" in meta else ""#"static" and such
	state_vars_scope = meta["state_vars_scope"] if "state_vars_scope" in meta else "local"#"local", "module"
	state_vars_storage = meta["state_vars_storage"] if "state_vars_storage" in meta else "stack"#"stack", "heap"

	lift_state_vars = state_vars_scope != "local"

	if state_vars_storage == "heap" :
		if state_vars_scope == "local" :
			st_v_scope = "static "
		else :
			st_v_scope = ""
	elif state_vars_storage == "stack" :
		st_v_scope = ""
	else :
		raise Exception("can't guess state vars storage")

	state_var_prefix = task_name + "_"
	state_vars = []
	for d in sorted(expd_dels.keys(), key=lambda x: expd_dels[x][0].nr) :
		del_out = expd_dels[d][1]
		del_type = types[del_out, del_out.terms[0], 0]
		if d.value[0] is None : #initializable delay
			state_vars.append("\t{4}{0} {1}del{2}_init = 0;{3}".format(
				core.VM_TYPE_BOOL, state_var_prefix, del_out.nr, linesep, st_v_scope))
			del_init = 0
		else :
			_, del_init = parse_literal(d.value[0], known_types=known_types, variables={})
		state_vars.append("\t{5}{0} {1}del{2} = {3};{4}".format(
			del_type, state_var_prefix, del_out.nr, del_init, linesep, st_v_scope))

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

	if endless_loop_wrap :
		loop_code = "\t" + (linesep + "\t").join(code)
	else :
		loop_code = linesep.join(("\tfor(;;)", "\t{", "\t\t" + (linesep + "\t\t").join(code), "\t}"))

	decl = ((function_prefix + " ") if function_prefix else "") + " ".join(("void", task_name, "()"))

	output = (((function_attributes + " ") if function_attributes else "") + decl + linesep + "{" + linesep +
		# locals and delays
		("" if lift_state_vars else "".join(state_vars)) +
		"".join(temp_vars + dummy_vars) +
		# main loop
		loop_code + linesep +
		"}")

	lifted_vars = tuple(state_vars) if lift_state_vars else tuple()

	return decl + ";", output, lifted_vars

#void loop()
#{
#	vm_dword_t next_scheduled_run = 0;
#	vm_dword_t next_t10_run, next_t50_run, ...;
#	vm_dword_t now;

#	for (;;) {

#		do {
#			idle_tsk_0();
#			idle_tsk_1();
#			...
#			now = time_ms();
#		} while ( now < next_scheduled_run );

#		next_scheduled_run = INT_MAX;

#		if ( now >= next_t10_run ) {
#			next_t10_run = now + 10;
#			if ( next_t10_run < next_scheduled_run ) {
#				next_scheduled_run = next_t10_run;
#			}
#			t10_tsk_0();
#			t10_tsk_1();
#			...
#		}

#		if ( now >= next_t50_run ) {
#			next_t50_run = now + 50;
#			if ( next_t50_run < next_scheduled_run ) {
#				next_scheduled_run = next_t50_run;
#			}
#			t50_tsk_0();
#			t50_tsk_1();
#			...
#		}
#		...
#	}
#}


def __churn_periodic_sched(tsk_groups, time_function, global_meta, tmr_data_type=core.VM_TYPE_WORD) :
	"""
	generate code for simple cooperative periodic task switching
	"""

	groups = dict(tsk_groups)

	if "idle" in groups :
		idle_group = groups.pop("idle")
	else :
		idle_group = []

	tmr_max = max(groups.keys()) if len(groups) else 0
	#2 ** ((8 * core.KNOWN_TYPES[tmr_data_type].size_in_bytes) - 1)

	timer_vars = [ "static {} next_{}_run = 0;".format(tmr_data_type, period)
		for period in sorted(groups.keys()) ]

	code = timer_vars

	code.append("{} now;".format(tmr_data_type))
	code.append("static {} next_scheduled_run = 0;".format(tmr_data_type))

	code.append("do {")
	for tsk_name in sorted(idle_group) :
		code.append("\t{}();".format(tsk_name))
	code.append("\tnow = {}();".format(time_function))
	code.append("} while ( (now - next_scheduled_run) < 0 );")

	code.append("next_scheduled_run = now + {};".format(tmr_max))

	for period, tasks in sorted(groups.items(), key=lambda i: i[0]) :
		tmr_var_name = "next_{}_run".format(period)
		code.append("if ( (now - {}) >= 0 ) {{".format(tmr_var_name))
		code.append("\t{} = now + {};".format(tmr_var_name, period))
		code.append("\tif ( {} <= next_scheduled_run ) {{".format(tmr_var_name))
		code.append("\t\tnext_scheduled_run = {};".format(tmr_var_name))
		code.append("\t}")
		for tsk_name in sorted(tasks) :
			code.append("\t{}();".format(tsk_name))
		code.append("}" + "")

	meta = dict(global_meta)
	meta["endless_loop_wrap"] = True

	vars_other = tuple() #XXX XXX XXX

	#code, types, tmp, tmp_args, expd_dels, global_vars, dummies, meta, known_types
	return code, {}, {}, {}, {}, [], [], meta, {}, vars_other


def churn_code(meta, global_vars, cg_out_list, include_files, tsk_groups, f) :
	"""
	generate code of module
	tasks_cg_out = [ (task_name, cg_out), ... ]
	f - writeble filelike object
	"""

	tsk_cg_out = list(cg_out_list)

	f.write("".join('#include "{0}"{1}'.format(incl, linesep) for incl in include_files))

	periodic_sched = "periodic_sched" in meta and meta["periodic_sched"]

	if periodic_sched :
		ps_cg_out = __churn_periodic_sched(tsk_groups, "millis", meta,
			tmr_data_type=core.VM_TYPE_WORD)
		tsk_cg_out.append(("loop", ps_cg_out))
#		print here(), churn_task_code("loop", ps_cg_out)

	decls = []
	functions = []
	variables = []
#	for name, cg_out in sorted(tsk_cg_out.items(), key=lambda x: x[0]) :
	for name, cg_out in tsk_cg_out :
#		print here(), name
		decl, func, lifted_vars = churn_task_code(name, cg_out)
		variables.extend(lifted_vars)
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
	f.write(linesep.join(variables))
	f.write(linesep.join(functions))
	f.write(linesep)




