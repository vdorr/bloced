
import random
from pprint import pprint
from implement import here, adjs_t
from collections import namedtuple


_vertex_t = namedtuple("_vertex_t", ("id", "value"))


def random_connections(g, vertex, max_terms, max_conns) :
# [ (t, t_nr, [ (b, t, t_nr), ...]), ... ]

	t_cnt = random.randint(0, max_terms)
	conn_cnt = random.randint(0, max_conns)

	nbh = [ (i, 0, [ x for x in conn_cnt ]) in range(t_cnt) ]

	#update referenced vertices

	return nbh

def random_graph(size) :
	random.seed()
	vertices = [ _vertex_t(i, random.randint(0, 2**31)) for i in range(size) ]

	g = { v : adjs_t([], []) for v in vertices }

	for v in vertices :
		g[v] = adjs_t(random_connections(g, v, 4, size / 3),
			random_connections(g, v, 4, size / 3))

	return g

#	return { v : adjs_t([], []) for v in vertices }


def a_star(g, a, b, h=lambda a, b: 1) :
	return []


if __name__ == "__main__" :
	g = random_graph(16)
	pprint(g)
	a = g.keys()[0]
	b = g.keys()[1]
	path = a_star(g, a, b)
	print path


