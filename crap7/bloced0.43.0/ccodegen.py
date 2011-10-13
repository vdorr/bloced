
import dfs
from os import linesep
import string
from functools import partial
#from itertools import groupby, chain, product, islice, dropwhile, count#, imap, ifilter, izip
from pprint import pprint
from implement import dft

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

expression = ""

def pre_visit(n) :
	global expression
	expression += " " + str(n) + "("

def post_visit(l, n) :
	global expression
	expression += ") "
	l.append(n)

def pre_tree(n) :
	global expression
	expression = ""
#	print "pre_tree"

def post_tree(n) :
	global expression
	print "post_tree:", expression

def codegen(g, conns, expd_dels, tsorted) :
	pprint(conns)
	l = []
	dft(g, conns, pre_visit, partial(post_visit, l), pre_tree, post_tree)
#	pprint(l)
	return "/* no code generated */"

# ------------------------------------------------------------------------------------------------------------

if __name__ == "__main__" :
	print("hello world")

# ------------------------------------------------------------------------------------------------------------

