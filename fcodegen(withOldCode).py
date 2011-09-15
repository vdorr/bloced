
import dfs
from os import linesep
import string
from functools import partial
from itertools import groupby, chain, product, islice, dropwhile, count#, imap, ifilter, izip
from pprint import pprint

# ------------------------------------------------------------------------------------------------------------

# convention: get_terms - last term in list is on top of stack
# assumption : every block is evaluated exactly once per iteration
#	- except constants
#	- evaluation of stateless components can (should) be optimized

# ------------------------------------------------------------------------------------------------------------

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

# ------------------------------------------------------------------------------------------------------------

def __gather_inputs(g, code, r, d, tmp, const, conns, v, inputs) :
	for t in inputs :
		if (v, t) in const :
			code.append(const.pop((v, t)))
		else :
			(slot_value, slot), = tuple(islice(dropwhile(lambda temp: not (v, t) in temp[0],
				zip(tmp, count())), 0, 1))
			code.append("tmp%i" % slot)
			#TODO tmp[slot] = ("empty",) if slot_value == (v, t) else slot_value - (v, t)
			#TODO tmp[slot] -= set((v, t))
			slot_value.remove((v, t))
			if not slot_value :
				tmp[slot] = ("empty",)

# ------------------------------------------------------------------------------------------------------------

def __manage_outputs(g, code, r, d, tmp, conns, v, outputs, still_needed) :
	for t in reversed(outputs) :
		if t in still_needed :
			if ("empty",) in tmp :
				slot = tmp.index(("empty",))
			else :
				slot = len(tmp)
				tmp.append(("empty",))
			tmp[slot] = list(conns[(v, t)])
			code.append("to tmp%i" % slot)
		else :
			code.append("drop")

# ------------------------------------------------------------------------------------------------------------

def codegen(g, conns, expd_dels, tsorted) :
	s = list(tsorted)
	code = []
	r = []
	d = []
	const = {}
	tmp = []

#	print "s"; pprint(s); print "conns"; pprint(conns)
	
	del_in = filter(lambda b: isinstance(b.prototype, dfs.DelayInProto), s)
	del_out = filter(lambda b: isinstance(b.prototype, dfs.DelayOutProto), s)
	#XXX in: out OR in: [out,] ? a) seem to be simpler to implement
	assert(list(set(del_in)) == del_in)
	assert([ i.nr for i in del_in ] == list(set([o.nr for o in del_out])) )
	delays = dict([ (i, filter(lambda o: o.nr == i.nr, del_out)) for i in del_in ]) #TODO test
	
	for i, outs in delays.iteritems() :
		#assert(s.index(i) > last_del_out_index)
		del_in_index = s.index(i)
		last_del_out_index = max([ s.index(o) for o in outs ])
		if del_in_index < last_del_out_index :
			s.insert(del_in_index, s.pop(last_del_out_index))

#	const = dict(chain(*
#		[ [ (cn, v.value) for cn in conns[(v, v.terms[0])] ]
#			for v in ifilter(lambda v: isinstance(v.prototype, dfs.ConstProto), s)]))
	const = dict(chain(*
		[ [ (cn, v.value) for cn in conns[(v, v.terms[0])] ]
			for v in s if isinstance(v.prototype, dfs.ConstProto)]))

#	for v in ifilter(lambda v: not isinstance(v.prototype, dfs.ConstProto), s) :
	for v in [ v for v in s if not isinstance(v.prototype, dfs.ConstProto) ] :
		loc = []
		inputs = filter(lambda t: t.direction == dfs.INPUT_TERM, v.terms)
		__gather_inputs(g, loc, r, d, tmp, const, conns, v, inputs)
		__execute(loc, v)
		outputs = filter(lambda t: t.direction == dfs.OUTPUT_TERM, v.terms)
		still_needed = filter(lambda t: (v, t) in conns, outputs)
		__manage_outputs(g, loc, r, d, tmp, conns, v, outputs, still_needed)
		code.append(string.join(loc, " "))

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
# ------------------------------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------------------------------

#def post_visit(g, code, tmp, d_stack, n) :

##	#gather inputs
##	for in_term, outputs in g[n].p :#XXX not reversed?
##		for sb, st in outputs :
##			if isinstance(sb.prototype, dfs.ConstProto) :
##				#push
##				pass
###			elif d_stack and d_stack[-1] == (sb, st) :
##			elif (sb, st) in d_stack :
##				stack_pos = d_stack.index((sb, st))
##				if stack_pos > 0 :
##					pass#nothing to do
##			elif (sb, st) in tmp :
##				(slot_value, slot), = tuple(islice(dropwhile(lambda temp: not (v, t) in temp[0],
##					zip(tmp, count())), 0, 1))
##				code.append("tmp%i" % slot)
##				#TODO tmp[slot] = ("empty",) if slot_value == (v, t) else slot_value - (v, t)
##				#TODO tmp[slot] -= set((v, t))
##				slot_value.remove((v, t))
##				if not slot_value :
##					tmp[slot] = ("empty",)
#...

from implement import dft_alt

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
	return reduce(lambda cnt, slot: cnt + (0 if slot == "empty" else 1), tmp, 0)

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
	if isinstance(m.prototype, dfs.ConstProto) :
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

	if isinstance(n.prototype, dfs.ConstProto) :
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

#	print("code=")
#	pprint(code)
#	pprint(l)
#	return string.join(code, linesep)
#	return "( no code generated )"

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


