
"""
non-compliant c header parser
"""

from pprint import pprint
#from collections import namedtuple
from utils import here

# ----------------------------------------------------------------------------


T_PREPROC = 1
T_COMMENT = 2
T_LINESEP = 3
T_SEMICOLON = 4
T_LEFT_BRACKET = 5
T_RIGHT_BRACKET = 6
T_COMMA = 7
T_CONTD = 8
T_OTHER = 9
T_PERIOD = 10


#tok_t = namedtuple("tok_t", ("type", "value"))


__SIMPLE_TOK = {
	"#" : T_PREPROC,
	";" : T_SEMICOLON,
	"(" : T_LEFT_BRACKET,
	")" : T_RIGHT_BRACKET,
	"," : T_COMMA,
	"." : T_PERIOD,
}


def __classify_token(tok, linesep) :
	assert(tok==tok.strip())
	assert(len(tok))
	if tok[0] in __SIMPLE_TOK :
		return (__SIMPLE_TOK[tok[0]], tok)
	elif tok == linesep :
		return (T_LINESEP, tok)
	elif tok.startswith("//") or (tok.startswith("/*") and tok.endswith("*/")):
		return (T_COMMENT, tok)
	else :
		return (T_OTHER, tok)


def is_declaration(l) :
	allowed = (T_COMMENT, T_OTHER)
	for tok_type, _ in l :

		if tok_type == T_LEFT_BRACKET :
			allowed = (T_COMMENT, T_OTHER, T_COMMA)
			continue
		elif tok_type == T_RIGHT_BRACKET :
			allowed = (T_SEMICOLON, )
			continue

		if not tok_type in allowed :
			return False
	return True


__DECL_TOK_TYPES = set((T_COMMENT, T_OTHER, T_COMMA, T_LEFT_BRACKET, T_RIGHT_BRACKET))


def extract_declarations(l) :
	hit = []
	for tok_type, tok in l :
		hit.append((tok_type, tok))
		if tok_type == T_SEMICOLON :
			if is_declaration(hit) :
				yield hit
			hit = []
		elif not tok_type in __DECL_TOK_TYPES :
			hit = []


def stripped_token_list(l) :
	return [ tok for _, tok in l ]


def drop_comments(l) :
	for tok_type, tok in l :
#		print here(), tok, tok_type
		if tok_type != T_COMMENT :
			yield tok_type, tok


def tokenize(s, linesep) :
	return stripped_token_list(tokenize2(s, linesep))


#TODO return eols, maybe
def tokenize2(s, linesep) :
	linesep = "\n"
	tok = ""
	sep = "*(),."
	in_comment = False
	prev = " "
	comment_end = ""
	for c in s :
		if c == "\r" :
			continue
		if ( prev + c ) == "/*" and not in_comment :
			in_comment = True
			comment_end = "*/"
		elif ( prev + c ) == "//" and not in_comment :
			in_comment = True
			comment_end = linesep
		elif in_comment and ( prev + c ).endswith(comment_end) :
			in_comment = False
			comment_end = None

		if c.isspace() and not in_comment:
			if tok :
				yield __classify_token(tok, linesep)
			tok = ""
		elif c in sep and not in_comment :
			if tok :
				yield __classify_token(tok, linesep)
				tok = ""
			yield __classify_token(c, linesep)
		else :
			tok += c
		prev = c
	if tok :
		yield __classify_token(tok, linesep)


def identify_type(lst) :
	return tuple(lst)
#	mods = ( "const", "volatile", "signed", "unsigned", "*" )
#	return join(lst, "_")


def parse_decl(tokens) :
#	print here(), tokens
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

