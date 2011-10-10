
import sys
from os import linesep
from pprint import pprint
from collections import namedtuple

# ----------------------------------------------------------------------------

#from string import split, join, strip
#from string import join, strip


def tokenize(s) :
	tokens = []
	tok = ""
	sep = "*(),"
	comment = False
	prev = " "
	comment_end = ""
	for c in s :
		if ( prev + c ) == "/*" and not comment :
			comment = True
			comment_end = "*/"
		elif ( prev + c ) == "//" and not comment :
			comment = True
		elif comment and ( prev + c ) == comment_end :
			comment = False

		if c.isspace() and not comment:
			if tok :
				tokens.append(tok)
			tok = ""
		elif c in sep and not comment :
			if tok :
				tokens.append(tok)
				tok = ""
			tokens.append(c)
		else :
			tok += c
		prev = c
	tokens.append(tok)
#	print tokens
	return tokens


def identify_type(lst) :
	return tuple(lst)
#	mods = ( "const", "volatile", "signed", "unsigned", "*" )
#	return join(lst, "_")


def parse(tokens) :
	arg_lst_start = tokens.index("(")
	name = tokens[arg_lst_start-1]
	ret_type = identify_type(tokens[0:arg_lst_start-1])
	args_list = []
	arg_type = []
	prev = None
	for tok in tokens[arg_lst_start+1:] :
		if tok in ( ",", ")" ) :
			t = identify_type(arg_type[:-1])
			if len(t) :
				args_list.append((t, prev))
			arg_type = []
		else :
			arg_type.append(tok)
		prev = tok
	return ret_type, name, args_list


def parse_header(s) :
	llines = s.split(";")
	for line in llines :
		tokens = tokenize(line)
		if tokens :
			ret_type, name, args_list = parse(tokens)
			#TODO generate gforth import
			#TODO generate comment on signature
			#TODO generate sysrq stub ( for imported function and optionaly for vm)
			print(ret_type, name, args_list)

# ----------------------------------------------------------------------------



VMEX_SIG = "_VM_EXPORT_"

known_types = {
	"vm_word_t" : (1, ),
	"vm_dword_t" : (2, ),
	"vm_float_t" : (2, ),
	"void" : (0, ),
}

def is_vmex_line(s) :
	ln = s.strip()
#	print(s.__class__)
	if not ln.startswith(VMEX_SIG) :
		return None
	return ln

def parse_vmex_line(s) :
	tokens = tokenize(s)
	if not tokens :
		return None
	ret_type, name, args_list = parse(tokens)
	return ret_type, name, args_list

term_type = namedtuple("term", (
#	"arg_index",
	"name",
#	"side", "pos",
	"direction", "variadic", "commutative", "type_name"))

def vmex_arg(a) :
	sig, name = a

#	TermModel arg_index, name, side, pos, direction, variadic, commutative, type_name=None
#	name,
	direction = OUTPUT_TERM if "*" in sig else INPUT_TERM
	variadic = False
	commutative = False
	(type_name, ) = [ tp for tp in sig if tp in known_types ]
	return term_type(name, direction, variadic, commutative, type_name)

def extract_exports(src_lines) :
#	exports = source.split(linesep)
	exports = [ parse_vmex_line(ln) for ln in
		[ is_vmex_line(ln) for ln in src_lines ] if ln != None ]

	for ret_type, name, args_list in exports :
#		print ret_type, name, args_list
		if ret_type[0] != VMEX_SIG :
			continue # should not happen
		vmex_ret_type = None
		for tp in ret_type :
			if tp in known_types :
				vmex_ret_type = tp
		outputs = [ (a_sig, a_name) for a_sig, a_name in args_list if "*" in a_sig ]
		if outputs :
			assert(vmex_ret_type == "void")
		inputs = [ a for a in args_list if not a in outputs ]
		assert(set(outputs+inputs)==set(args_list))

		terms_in = [ vmex_arg(a) for a in inputs ]
		terms_out = [ vmex_arg(a) for a in outputs ] if outputs else vmex_arg((ret_type, "out"))
		print terms_in, terms_out

		#TermModel arg_index, name, side, pos, direction, variadic, commutative, type_name=None

	return exports

if __name__ == "__main__" :
	OUTPUT_TERM, INPUT_TERM = 666, 667
	if len(sys.argv) == 1 :
		source = "iowrap.h"
	else :
		source = sys.argv[1]
	srcf = open(source, "r")
#	pprint(dir(srcf.read()))
	srcs = srcf.readlines()
#	print(srcs)
	srcf.close()

	exports = extract_exports(srcs)
#	for ln in exports :
#		print ln

