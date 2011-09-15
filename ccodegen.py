
import dfs
from dfs import INPUT_TERM, OUTPUT_TERM
import core
from os import linesep
import string
from functools import partial
from itertools import count, groupby
from pprint import pprint
from implement import dft_alt, get_terms_flattened, sethi_ullman, temp_init, get_tmp_slot, add_tmp_ref, pop_tmp_ref, tmp_used_slots

# ------------------------------------------------------------------------------------------------------------

#def pre_visit(g, numbering, subtrees, n, visited, terms_to_visit) :
#	number, indices = numbering[n]
##	depth_limit = 32
##	if number > depth_limit :
##		pass # XXX now what?
#	ordering = dict(zip(terms_to_visit, indices))
#	terms_to_visit.sort(key=lambda t: ordering[t])

# ------------------------------------------------------------------------------------------------------------

#def pre_dive(code, tmp, subtrees, n, nt, nt_nr, m, mt, mt_nr, visited) :
###	current_expression = expression[-1]
##	expression.append(((n, nt, nt_nr), ""))
###	print "pre_dive:", n, nt, nt_nr, "->", m, mt, mt_nr
#	pass

# ------------------------------------------------------------------------------------------------------------

## single input preparation
#def post_dive(g, code, tmp, subtrees, n, nt, nt_nr, m, mt, mt_nr, visited) :
##	current_expression = expression.pop()#[-1]
##	expr_for_term = current_expression[0]
###	print "post_dive:", (n, nt, nt_nr), expr_for_term
##	assert((n, nt, nt_nr) == expr_for_term)

###	print "post_dive:", n, nt, nt_nr, "<-", m, mt, mt_nr

##	outputs = g[m].s
###out_term, out_t_nr, succs = outputs[0]
##	if len(outputs) == 1 and len(outputs[0][2]) == 1 : # single out, single successor
###		print "\tembedable"
##		pass
##	else :
##		pass
###		code.append(expr)


###	if isinstance(m.prototype, core.ConstProto) :
###		code.append(str(m.value))
####		print "post_dive:", n, nt, "<-", m, mt, "code:", str(m.value)
###	elif (m, mt, mt_nr) in subtrees :
###		subtrees.remove((m, mt, mt_nr))
####		pop_tmp_ref(tmp, n, nt, nt_nr)
####		print "post_dive:", n, nt, "<-", m, mt, "code:", "nop, d stack"
###	else :
###		slot = pop_tmp_ref(tmp, n, nt, nt_nr)
###		if slot != None:
###			code.append("tmp%i" % slot)
####			print "post_dive:", n, nt, "<-", m, mt, "code:", "tmp%i" % slot
###		else :
###			raise Exception("holy shit!")
####	print "post_dive:", n, nt, "<-", m, mt, "code[-1]=", code[-1]
#	pass

# ------------------------------------------------------------------------------------------------------------

# execution
def post_visit(g, code, tmp, subtrees, n, visited) :

#TODO can i get rid off som cycles by use of other callbacks?
	if isinstance(n.prototype, core.ConstProto) :
		return None # handled elsewhere

##	print n, "!"
#	if isinstance(v.prototype, core.DelayInProto) :
#		code.append("to del%i" % v.nr)
#	elif isinstance(v.prototype, core.DelayOutProto) :
#		code.append("del%i" % v.nr)
#	else :
#		code.append(v.prototype.exe_name)



	inputs, outputs = g[n]
#	assert(outputs == g[n].s)
#	assert(inputs == g[n].p)

	args = []
	outs = []

#	print n

	#gather inputs
	for in_term, in_t_nr, preds in inputs :
		assert(len(preds)==1)
		((m, m_t, m_t_nr), ) = preds
#		print "\tgathering:", m, m_t, m_t_nr, "for", (n, in_term, in_t_nr), "subtrees:", subtrees
		if isinstance(m.prototype, core.ConstProto) :
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

#	print "\targs:", args

	if isinstance(n.prototype, core.DelayInProto) :
		exe_name = "set_del%i" % n.nr
	elif isinstance(n.prototype, core.DelayOutProto) :
		exe_name = "get_del%i" % n.nr
	else :
		exe_name = n.prototype.exe_name

	expr = exe_name + "(" + string.join(args, ", ") + string.join(outs, ", ") + ")"
	is_expr = len(outputs) == 1 and len(outputs[0][2]) == 1

#	print "\texpr:", expr, "is_expr:", is_expr


	if is_expr :

		((out_term, out_t_nr, succs), ) = outputs
		subtrees[succs[0]] = expr

		assert(len(outputs)==1 and len(outputs[0][2])==1)
#		print "yyy:", outputs[0][2]
		subtrees[outputs[0][2][0]] = expr
	else :


		for out_term, out_t_nr, succs in outputs :
			slot = add_tmp_ref(tmp, list(succs))


		if len(outputs) == 0 :
			code.append(expr + ";")
		elif len(outputs) == 1 :
#			code.append("tmpXXX = " + expr + ";")
			code.append("tmp%i = %s;" % (slot, expr))
			#TODO add tmp refs
		else :
			code.append(expr + ";")

#	if is_expr : # single out, single successor
#		((out_term, out_t_nr, succs), ) = outputs
#		subtrees[succs[0]] = expr
#	else :
#		for out_term, out_t_nr, succs in outputs :
#			slot = add_tmp_ref(tmp, list(succs))




##			print "out_term, succs", out_term, succs
#			if len(succs) == 1 :
#				if len(n.prototype.outputs) == 1 :
##					d_stack.append((n, out_term, out_t_nr))
#					pass
#				else :
##					slot = add_tmp_ref(tmp, list(succs))
##					code.append("to tmp%i" % slot)
#					pass
##			elif len(succs) > 1 :
##				if len(n.prototype.outputs) == 1 :
##					code.append("dup")
##					d_stack.append((n, out_term, out_t_nr))
##				slot = add_tmp_ref(tmp, list(succs))
##				code.append("to tmp%i" % slot)
##			else :
##				code.append("drop")


# ------------------------------------------------------------------------------------------------------------

#def pre_tree(g, code, tmp, subtrees, n, visited) :
##	assert(len(d_stack)==0)
#	pass

# ------------------------------------------------------------------------------------------------------------

#def post_tree(g, code, tmp, subtrees, n, visited) :
#	for i, ex in subtrees.items() :
#		print "post_tree:", i , ex
##	assert(len(d_stack)==0)
#	pass

# ------------------------------------------------------------------------------------------------------------

def codegen_alt(g, expd_dels, meta) :

#	pprint(g)

#	numbering = sethi_ullman(g)

	tmp = temp_init()
	subtrees = {}
	code = []
	dft_alt(g,
#		partial(pre_visit, g, numbering, subtrees),
#		partial(pre_dive, code, tmp, subtrees),
#		partial(post_dive, g, code, tmp, subtrees),
		post_visit = partial(post_visit, g, code, tmp, subtrees),
#		partial(pre_tree, g, code, tmp, subtrees),
#		partial(post_tree, g, code, tmp, subtrees)
	)

	assert(tmp_used_slots(tmp) == 0)
	assert(len(subtrees) == 0)

	variables = ([ "del%i = %i" % (i, int(d.value))
			for d, i in zip(sorted(expd_dels.keys(), lambda x,y: y.nr-x.nr), count()) ] +
		     [ "tmp%i" % i for i in range(len(tmp)) ])

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


