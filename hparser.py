
import sys
import os
from pprint import pprint
from collections import namedtuple

# ----------------------------------------------------------------------------

__linesep = os.linesep

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
			comment_end = __linesep
		elif comment and ( prev + c ).endswith(comment_end) :
			comment = False
			comment_end = None

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

def parse_decl(tokens) :
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

# ----------------------------------------------------------------------------

