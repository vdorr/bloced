
import dfs
from os import linesep
import string
from functools import partial
#from itertools import groupby, chain, product, islice, dropwhile, count#, imap, ifilter, izip
from pprint import pprint

# ------------------------------------------------------------------------------------------------------------

#XXX really?
__comp_stub = """
void comp_%s() {
}
"""

__prog_stub = """
/* hello world */

int main() {
	while (1) {
		setup();
		loop_forever();
	}
	return 666;
}
"""

# ------------------------------------------------------------------------------------------------------------

__infix_ops = {
	"xor" : "^",
	"and" : "&",
	"or" : "|",
}

__prefixed_infix_ops = {
	"nand" : "!",
	"nor" : "!",
}

def __execute(code, v) :
#	if isinstance(v.prototype, dfs.ConstProto) :
#		code.append(str(v.value))
	if isinstance(v.prototype, dfs.DelayInProto) :
		code.append("to del%i" % v.nr)
	elif isinstance(v.prototype, dfs.DelayOutProto) :
		code.append("del%i" % v.nr)
	else :
#		print v, "exename:", v.prototype.exe_name
		code.append(v.prototype.exe_name)

#def __executable(n) :
#	if isinstance(v.prototype, dfs.ConstProto) :
#		return str(v.value)
#	if isinstance(v.prototype, dfs.DelayInProto) :
#		code.append("to del%i" % v.nr)
#	elif isinstance(v.prototype, dfs.DelayOutProto) :
#		code.append("del%i" % v.nr)
#	else :
##		print v, "exename:", v.prototype.exe_name
#		code.append(v.prototype.exe_name)

# ------------------------------------------------------------------------------------------------------------

#TODO
def __get_tmp_range(tmp, outdegree) :
	return [ __get_tmp_slot(tmp) for _ in range(outdegree) ]

def __get_tmp_slot(tmp) :
	if "empty" in tmp :
		slot = tmp.index("empty")
	else :
		slot = len(tmp)
		tmp.append("empty")
	return slot

def __add_tmp_ref(tmp, refs) :
	slot = __get_tmp_slot(tmp)
	tmp[slot] = list(refs)
	return slot

def __pop_tmp_ref(tmp, b, t) :
	for slot, nr in zip(tmp, count()) :
		if slot != "empty" and (b, t) in slot :
			slot.remove((b, t))
			if not slot :
				slot = "empty"
			return nr
	return None

# ------------------------------------------------------------------------------------------------------------

def pre_visit(g, code, tmp, args, n, visited) :
	args.append((n, []))

#	if isinstance(n.prototype, dfs.ConstProto) :
#		expression += "" + n.value + ""
#	elif isinstance(n.prototype, dfs.DelayInProto) :
#		pass#code.append("to del%i" % v.nr)
#	elif isinstance(n.prototype, dfs.DelayOutProto) :
#		pass#code.append("del%i" % v.nr)
#	else :
#		expression += " " + n.prototype.exe_name + "("

# single input preparation
def post_dive(g, code, tmp, args, n, nt, m, mt, visited) :
#	print "post_dive:", n, nt, "<-", m, mt
#	print "post_dive:", n, m, args[-1]
	b, alist = args[-1]
	assert(b == n)
#	alist.append( (n, nt) )

	if isinstance(m.prototype, dfs.ConstProto) :
		alist.append(str(m.value))
	elif isinstance(m.prototype, dfs.DelayOutProto) :
		alist.append("del%i" % m.nr)
	else :
		pass
#		alist.append(m.prototype.exe_name)
#		expression += " " + n.prototype.exe_name + "("

	pass

# execution
def post_visit(g, code, tmp, args, n, visited) :
#	print "topological ordering:", n


	b, alist = args.pop(-1)
	assert(b == n)
	
	print b, "alist", alist
	assert(len(alist) == len(n.prototype.inputs))

	if isinstance(n.prototype, dfs.ConstProto) or isinstance(n.prototype, dfs.DelayOutProto) :
		return None # handled elsewhere
	elif isinstance(n.prototype, dfs.DelayInProto) :
		exename = "delIn"
	else :
		exename = n.prototype.exe_name

	if len(b.prototype.outputs) > 1 :
		outvars = string.join([ "&r%i" % i for i in range(len(b.prototype.outputs)) ], ", ")
	else :
		outvars = False




	outputs = g[n].s
	for out_term, succs in outputs :
#		print "out_term, succs", out_term, succs
		if len(succs) == 1 :
			if len(n.prototype.outputs) == 1 :
				d_stack.append((n, out_term))
			else :
				slot = __add_tmp_ref(tmp, list(succs))
				code.append("to tmp%i" % slot)
			pass # store on d stack, OR NO!?! (allways) possible only with single-output block
		elif len(succs) > 1 :
			if len(n.prototype.outputs) == 1 :
				code.append("dup")
#				print "post_visit, leaving on d:", succs[0]
				d_stack.append((n, out_term))
			slot = __add_tmp_ref(tmp, list(succs)) #XXX including one to be taken from d, not good
			code.append("to tmp%i" % slot)
			pass # leading to multiple inputs, store in temp
		else :
			code.append("drop")
			pass # not needed, drop






	invocation = exename + "(" + string.join(alist, ", ") + ((", " + outvars) if outvars else "") +")"
	if len(args) == 0 : # root reached
		code.append(invocation)
		print "code=", code
	else :
		b, alist = args[-1]
		alist.append(invocation)

	return None

##	values = { ( block, in_term) : expression, ... }
##	list should be better, but this is easier to comprehend
##	values = {}
#	my_args = [ args.pop((n, i)) for i in n.prototype.inputs ]
##	my_args = [] #XXX

#	if isinstance(n.prototype, dfs.ConstProto) :
#		stmt = str(n.value)
#	else :
#		bname = n.prototype.type_name
#		if bname in __infix_ops :
#			prefix = __prefixed_infix_ops[bname] if bname in __prefixed_infix_ops else ""
#			stmt = prefix + "(" + string.join(my_args, " " + __infix_ops[bname] + " ")
#		else :
#			stmt = bname + "(" + string.join(my_args, ",")

#	print "stmt=", stmt


#	outdegree = len(n.prototype.outputs)

#	assert((not bname in __infix_ops ) if not outdegree in (0, 1) else True)# extremely paranoid sanity check

##	args = []

#	for out_term in n.prototype.outputs :
#		args[n, out_term]

#	if outdegree in (0, 1) :
#		# keep nesting
##		args.append(stmt)
#		pass
#	else :
#		# stop nesting, emit one line statement, start another

#		# get tmp slots
#		slot_nrs = __get_tmp_range(tmp, outdegree)
#		stmt += (", " if my_args else "") + string.join(", ", [ "&tmp%i" % nr for nr in slot_nrs ]) + ")"

#		code.append(stmt)
##		args = []

		


def pre_tree(g, code, tmp, args, n, visited) :
	pass

def post_tree(g, code, tmp, args, n, visited) :
	assert(len(args) == 0)
	pass

def pre_dive(code, tmp, n, nt, m, mt, visited) :
	pass

# ------------------------------------------------------------------------------------------------------------

from implement import dft_alt

def codegen_alt(g, expd_dels, meta) :
	tmp = []
	args = []
	code = []
	dft_alt(g,
		partial(pre_visit, g, code, tmp, args),
		partial(pre_dive, code, tmp),
		partial(post_dive, g, code, tmp, args),
		partial(post_visit, g, code, tmp, args),
		partial(pre_tree, g, code, tmp, args),
		partial(post_tree, g, code, tmp, args))
	return "/* no code generated */"

# ------------------------------------------------------------------------------------------------------------

def codegen(g, conns, expd_dels, tsorted) :
#	pprint(conns)
#	l = []
#	dft(g, conns, pre_visit, partial(post_visit, l), pre_tree, post_tree)
##	pprint(l)
	return "/* no code generated */"

# ------------------------------------------------------------------------------------------------------------

if __name__ == "__main__" :
	pass

# ------------------------------------------------------------------------------------------------------------

