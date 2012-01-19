
import pickle
from itertools import count, dropwhile, islice
import dfs
import core
from pprint import pprint

# ------------------------------------------------------------------------------------------------------------

#TODO elaborate docstring
#TODO own exceptions
#TODO top level dict container for sub-sheets and metadata and/or resources

# ------------------------------------------------------------------------------------------------------------

def pickle_dfs_model(m, f) :
	try :
		pickle.dump(get_dfs_model_data(m), f)
	except pickle.PickleError :
		print("PickleError")
		raise

# ------------------------------------------------------------------------------------------------------------

def unpickle_dfs_model(f, lib=None) :
	try :
		types, struct, meta = pickle.load(f)
#		pprint((types, struct, meta))
		return restore_dfs_model(types, struct, meta, lib)
	except pickle.PickleError :
		print("PickleError")
		raise

# ------------------------------------------------------------------------------------------------------------

#TODO for use with clipboard and undo pass blocks and other components separately
#TODO move to dfs.py
#TODO import/export filters? (could be used to suck in something completely different, or to generate some completely different shit)
def get_dfs_model_data(m) :
	return get_dfs_model_data2(m.blocks, m.connections, m.connections_meta, dfs.GraphModel.get_meta(m))

# ------------------------------------------------------------------------------------------------------------

def term_nfo(t0) :
	return (t0[0].name, t0[1]) if isinstance(t0, tuple) else t0.name

def get_dfs_model_data2(blocks, connections, connections_meta, model_meta) :

	n = dict(zip(blocks, count()))

	struct = [ ((n[b0], term_nfo(t0)), [ (n[b1], term_nfo(t1)) for b1, t1 in vals ])
			for (b0, t0), vals in connections.items() ]

	types = [ (nr, block.prototype.type_name) for block, nr in n.iteritems() ]

	conn_meta = [ ((n[b0], term_nfo(t0), n[b1], term_nfo(t1)), v)
		for (b0, t0, b1, t1), v in connections_meta.items() ]

	meta = (
		model_meta,
		{ n[b] : dfs.BlockModel.get_meta(b) for b in blocks },
		conn_meta
	)
	return types, struct, meta

# ------------------------------------------------------------------------------------------------------------

def restore_dfs_model(types, struct, meta, lib) :
	m = dfs.GraphModel()
	m.enable_logging = False
	fact = core.create_block_factory() if lib is None else lib
	load_to_dfs_model(m, types, struct, meta, fact, deserializing=True)
	m.enable_logging = True
	return m

# ------------------------------------------------------------------------------------------------------------

def stname(t0) :
	return t0[0] if isinstance(t0, tuple) else t0

def load_to_dfs_model(m, types, struct, meta, fact, deserializing=False) :

	if len(meta) == 2 :
		graph_meta, block_meta, = meta
		conn_meta = {} #TODO
	else :
		graph_meta, block_meta, cnm = meta
		conn_meta = dict(cnm)
		
	block_meta = dict(block_meta)#XXX XXX

	blocks = {}
	for n, type_name in types :
		t = fact.get_block_by_name(type_name)
		b = dfs.BlockModel(t, m)
		b.set_meta(block_meta[n])
		blocks[n] = b
		m.add_block(b)

	conn_list = []
	for (block_nr, term_name), conns in struct :
		sb = blocks[block_nr]

		t_name = stname(term_name)
		st, = tuple(islice(dropwhile(lambda t: t.name != t_name, sb.terms), 0, 1))

		if isinstance(term_name, tuple) :
			st = (st, term_name[1])

		for ntb, stt in conns :

			tb = blocks[ntb]

			stt_name = stname(stt)
			tt, = tuple(islice(dropwhile(lambda t: t.name != stt_name, tb.terms), 0, 1))
			
			meta = (conn_meta[(block_nr, term_name, ntb, stt)] 
				if (block_nr, term_name, ntb, stt) in conn_meta else {})

			tt2 = (tt, stt[1]) if isinstance(stt, tuple) else tt #XXX check this if problem with varterm occurs!
			m.add_connection(sb, st, tb, tt2, meta=meta, deserializing=deserializing)

			conn_list.append((sb, st, tb, tt2))

	return blocks.values(), conn_list

CONTAINER_VERSION = (0, 0, 1)

def pickle_workbench(wrk, f) :
	try :
		pickle.dump(get_workbench_data(wrk), f)
	except pickle.PickleError :
		print("PickleError")
		raise


def get_workbench_data(w) :
#XXX make it stable! same model -> same blob, bit by bit

	global_meta = {}
	toc = []
	resources = []

	for sheet in w.get_sheets() :
		get_dfs_model_data(sheet)

	return (CONTAINER_VERSION, global_meta, tuple(toc), tuple(resources))


def unpickle_workbench(f, lib=None) :
	try :
		types, struct, meta = pickle.load(f)
#		pprint((types, struct, meta))
		return restore_dfs_model(types, struct, meta, lib)
	except pickle.PickleError :
		print("PickleError")
		raise





