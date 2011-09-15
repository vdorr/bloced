
import dfs
import core
from os import linesep
import string
from functools import partial
from itertools import count
from pprint import pprint
from implement import dft_alt

# ------------------------------------------------------------------------------------------------------------

#TODO TODO TODO revisit
# convention: get_terms - last term in list is on top of stack
# assumption : every block is evaluated exactly once per iteration
#	- except constants
#	- evaluation of stateless components can (should) be optimized

# ------------------------------------------------------------------------------------------------------------

#TODO should be better to use dictionary

# TODO may have limit parameter and generate spill code
def __temp_init() :
	return []

# ------------------------------------------------------------------------------------------------------------

def __get_tmp_slot(tmp) :
	if "empty" in tmp :
		slot = tmp.index("empty")
	else :
		slot = len(tmp)
		tmp.append("empty")
	return slot

# ------------------------------------------------------------------------------------------------------------

def __add_tmp_ref(tmp, refs) :
	slot = __get_tmp_slot(tmp)
	tmp[slot] = list(refs)
	return slot

# ------------------------------------------------------------------------------------------------------------

def __pop_tmp_ref(tmp, b, t) :
#	print "tmp=", tmp, "searching:", b, t
	for slot, nr in zip(tmp, count()) :
#		print "\tslot[", nr, "]=", slot
		if slot != "empty" and (b, t) in slot :
			slot.remove((b, t))
			if len(slot) == 0 :
				tmp[nr] = "empty"
			return nr
	return None

# ------------------------------------------------------------------------------------------------------------

def __tmp_used_slots(tmp) :
	assert( sum([ 1 for slot in tmp if slot != "empty"])== reduce(lambda cnt, slot: cnt + (0 if slot == "empty" else 1), tmp, 0))
	return sum([ 1 for slot in tmp if slot != "empty" ])

# ------------------------------------------------------------------------------------------------------------

def __execute(code, v) :
#	if isinstance(v.prototype, core.ConstProto) :
#		code.append(str(v.value))
	if isinstance(v.prototype, core.DelayInProto) :
		code.append("to del%i" % v.nr)
	elif isinstance(v.prototype, core.DelayOutProto) :
		code.append("del%i" % v.nr)
	else :
#		print v, "exename:", v.prototype.exe_name
		code.append(v.prototype.exe_name)

# ------------------------------------------------------------------------------------------------------------

def pre_visit(n, visited) :
	pass#nothing? really?

# ------------------------------------------------------------------------------------------------------------

def pre_dive(code, tmp, n, nt, m, mt, visited) :
#	print "pre_dive:", n, nt, m, mt
	pass

# ------------------------------------------------------------------------------------------------------------

# single input preparation
def post_dive(g, code, tmp, d_stack, n, nt, m, mt, visited) :
#	print "post_dive:", n, nt, "<-", m, mt
#	assert(n in visited)
#	assert(m in visited)
#	print "d_stack=", d_stack, "(n, nt)=", (n, nt)
	if isinstance(m.prototype, core.ConstProto) :
		code.append(str(m.value))
#		print "post_dive:", n, nt, "<-", m, mt, "code:", str(m.value)
	elif (m, mt) in d_stack : #XXX or (n, nt) == d_stack[-1] ??!?!? nope, it is equal
		d_stack.remove((m, mt))
		__pop_tmp_ref(tmp, n, nt)
#		print "post_dive:", n, nt, "<-", m, mt, "code:", "nop, d stack"
	else :
		slot = __pop_tmp_ref(tmp, n, nt)
		if slot != None:
			code.append("tmp%i" % slot)
#			print "post_dive:", n, nt, "<-", m, mt, "code:", "tmp%i" % slot
		else :
			raise Exception("holy shit!")
#	print "post_dive:", n, nt, "<-", m, mt, "code[-1]=", code[-1]

# ------------------------------------------------------------------------------------------------------------

# execution
def post_visit(g, code, tmp, d_stack, n, visited) :

	if isinstance(n.prototype, core.ConstProto) :
		return None # handled elsewhere

#	print n, "!"
	__execute(code, n)

	#manage outputs
	outputs = g[n].s
	for out_term, succs in outputs :
#		print "out_term, succs", out_term, succs
		if len(succs) == 1 :
			if len(n.prototype.outputs) == 1 :
#XXX				d_stack.append(succs[0])
				d_stack.append((n, out_term))
			else :
				slot = __add_tmp_ref(tmp, list(succs))
				code.append("to tmp%i" % slot)
			pass # store on d stack, OR NO!?! (allways) possible only with single-output block
		elif len(succs) > 1 :
			if len(n.prototype.outputs) == 1 :
				code.append("dup")
#				print "post_visit, leaving on d:", succs[0]
#XXX				d_stack.append(succs[0])
				d_stack.append((n, out_term))
			slot = __add_tmp_ref(tmp, list(succs)) #XXX including one to be taken from d, not good
			code.append("to tmp%i" % slot)
			pass # leading to multiple inputs, store in temp
		else :
			code.append("drop")
			pass # unconnected, drop

# ------------------------------------------------------------------------------------------------------------

def pre_tree(g, code, tmp, d_stack, n, visited) :
	assert(len(d_stack)==0)
	pass # expression = ""

# ------------------------------------------------------------------------------------------------------------

def post_tree(g, code, tmp, d_stack, n, visited) :
	assert(len(d_stack)==0)
	pass # print "post_tree:", expression

# ------------------------------------------------------------------------------------------------------------

def an_pre_visit(n, visited) :
	pass

def an_pre_dive(n, nt, m, mt, visited) :
	pass

def an_post_dive(n, nt, m, mt, visited) :
	pass

def an_post_visit(n, visited) :
	pass

def an_pre_tree(n, visited) :
	pass

def an_post_tree(n, visited) :
	pass

def __analyze(g, expd_dels, meta) :
	# analyze d,r and spill usage
	# create sethi-ullman numbering, sort of
	dft_alt(g,
		partial(an_pre_visit),
		partial(an_pre_dive),
		partial(an_post_dive),
		partial(an_post_visit),
		partial(an_pre_tree),
		partial(an_post_tree))

# ------------------------------------------------------------------------------------------------------------

def codegen_alt(g, expd_dels, meta) :

	tmp = __temp_init()
	d_stack = []
	code = []
	dft_alt(g,
		pre_visit,
		partial(pre_dive, code, tmp),
		partial(post_dive, g, code, tmp, d_stack),
		partial(post_visit, g, code, tmp, d_stack),
		partial(pre_tree, g, code, tmp, d_stack),
		partial(post_tree, g, code, tmp, d_stack))

	assert(__tmp_used_slots(tmp) == 0)

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


