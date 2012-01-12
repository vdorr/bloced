
import dfs
from dfs import INPUT_TERM, OUTPUT_TERM
import core
from os import linesep
from functools import partial
from itertools import count, groupby
from pprint import pprint
from implement import *

# ------------------------------------------------------------------------------------------------------------

def pre_visit(g, numbering, n, visited, terms_to_visit) :
	number, indices = numbering[n]
	ordering = dict(zip(terms_to_visit, indices))
	terms_to_visit.sort(key=lambda t: ordering[t])

# ------------------------------------------------------------------------------------------------------------

def pre_dive(code, tmp, n, nt, nt_nr, m, mt, mt_nr, visited) :
	pass

# ------------------------------------------------------------------------------------------------------------

# single input preparation
def post_dive(g, code, tmp, d_stack, n, nt, nt_nr, m, mt, mt_nr, visited) :
#	print "post_dive:", n, nt, "<-", m, mt
#	assert(n in visited)
#	assert(m in visited)
#	print "d_stack=", d_stack, "(n, nt)=", (n, nt)
	if isinstance(m.prototype, core.ConstProto) :
		assert(m.value != None)
		code.append(str(m.value))
#		print "post_dive:", n, nt, "<-", m, mt, "code:", str(m.value)
	elif (m, mt, mt_nr) in d_stack : #XXX or (n, nt) == d_stack[-1] ??!?!? nope, it is equal
		d_stack.remove((m, mt, mt_nr))
		pop_tmp_ref(tmp, n, nt, nt_nr)
#		print "post_dive:", n, nt, "<-", m, mt, "code:", "nop, d stack"
	else :
		slot = pop_tmp_ref(tmp, n, nt, nt_nr)
		if slot != None:
			code.append("tmp%i" % slot)
#			print "post_dive:", n, nt, "<-", m, mt, "code:", "tmp%i" % slot
		else :
			raise Exception("holy shit!")
#	print "post_dive:", n, nt, "<-", m, mt, "code[-1]=", code[-1]

# ------------------------------------------------------------------------------------------------------------

# execution
def post_visit(g, code, tmp, d_stack, expd_dels, n, visited) :

#	print "post_visit", n, n.prototype

	if isinstance(n.prototype, core.ConstProto) :
		return None # handled elsewhere

	if isinstance(n.prototype, core.DelayInProto) :
		del_in, del_out = expd_dels[n.delay]
#		print 1
		if not del_out in visited :
#			print 2
			slot = add_tmp_ref(tmp, [ (del_in, del_in.terms[0], 0) ])
			code.append("del%i to tmp%i" % (n.nr, slot))
		code.append("to del%i" % n.nr)
	elif isinstance(n.prototype, core.DelayOutProto) :
		del_in, del_out = expd_dels[n.delay]
		if del_in in visited :
			slot = pop_tmp_ref(tmp, del_in, del_in.terms[0], 0)
			code.append("tmp%i" % slot)
		else :
			code.append("del%i" % n.nr)
	else :
		assert(n.prototype.exe_name != None)
		code.append(n.prototype.exe_name)

	#manage outputs
	outputs = g[n].s
	for out_term, out_t_nr, succs in outputs :
#		print "out_term, succs", out_term, succs
		if len(succs) == 1 :
			if len(n.prototype.outputs) == 1 :
#XXX				d_stack.append(succs[0])
				d_stack.append((n, out_term, out_t_nr))
			else :
				slot = add_tmp_ref(tmp, list(succs))
				code.append("to tmp%i" % slot)
			pass # store on d stack, OR NO!?! (allways) possible only with single-output block
		elif len(succs) > 1 :
			if len(n.prototype.outputs) == 1 :
				code.append("dup")
#				print "post_visit, leaving on d:", succs[0]
#XXX				d_stack.append(succs[0])
				d_stack.append((n, out_term, out_t_nr))
#			print "list(succs)=", list(succs)
			slot = add_tmp_ref(tmp, list(succs)) #XXX including one to be taken from d, not good
			code.append("to tmp%i" % slot)
			pass # leading to multiple inputs, store in temp
		else :
			code.append("drop")# unconnected, drop

# ------------------------------------------------------------------------------------------------------------

def pre_tree(g, code, tmp, d_stack, n, visited) :
	assert(len(d_stack)==0)

# ------------------------------------------------------------------------------------------------------------

def post_tree(g, code, tmp, d_stack, n, visited) :
	assert(len(d_stack)==0)

# ------------------------------------------------------------------------------------------------------------

def codegen_alt(g, expd_dels, meta, types) :

	numbering = sethi_ullman(g)
	tmp = temp_init()
	d_stack = []
	code = []
	dft_alt(g,
		partial(pre_visit, g, numbering),
		partial(pre_dive, code, tmp),
		partial(post_dive, g, code, tmp, d_stack),
		partial(post_visit, g, code, tmp, d_stack, expd_dels),
		partial(pre_tree, g, code, tmp, d_stack),
		partial(post_tree, g, code, tmp, d_stack))

	assert(tmp_used_slots(tmp) == 0)

#	del_init = [ "%i " % int(d.value) for d in sorted(expd_dels.keys(), key=lambda x,y: y.nr-x.nr) ]
	del_init = [ "%i " % int(d.value) for d in sorted(expd_dels.keys(), key=lambda x: expd_dels[x][0].nr, reverse=True) ]
	output = (": tsk" + linesep +
		# locals and delays
		("\t" + "".join(del_init) + ("0 " * tmp_max_slots_used(tmp)) + linesep +
		("\tlocals| " + ("del%i " * len(del_init)) % tuple(range(len(del_init))) +
		("tmp%i " * tmp_max_slots_used(tmp)) % tuple(range(tmp_max_slots_used(tmp))) + "|" + linesep)
		if ( len(tmp) or len(del_init) ) else "")+
		# main loop
		"\tbegin" + linesep +
		linesep.join([ "\t\t" + loc for loc in code ]) + linesep +
		"\tagain" + linesep + ";")

	return output

# ------------------------------------------------------------------------------------------------------------


