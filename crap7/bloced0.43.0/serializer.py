
import pickle
from itertools import count, dropwhile, islice
import dfs
from pprint import pprint

# ------------------------------------------------------------------------------------------------------------

#TODO elaborate docstring
#TODO own exceptions

# ------------------------------------------------------------------------------------------------------------

def pickle_dfs_model(m, f) :
	try :
		pickle.dump(get_dfs_model_data(m), f)
	except pickle.PickleError :
		print("PickleError")
		raise

# ------------------------------------------------------------------------------------------------------------

def unpickle_dfs_model(f) :
	try :
		types, struct, meta = pickle.load(f)
		return restore_dfs_model(types, struct, meta)
	except pickle.PickleError :
		print("PickleError")
		raise

# ------------------------------------------------------------------------------------------------------------

#TODO for use with clipboard and undo pass blocks and other components separately
#TODO move to dfs.py
#TODO import/export filters? (could be used to suck in something completely different, or to generate some completeley different shit)
def get_dfs_model_data(m) :
	return get_dfs_model_data2(m.blocks, m.connections, m.connections_meta, dfs.GraphModel.get_meta(m))

# ------------------------------------------------------------------------------------------------------------

def get_dfs_model_data2(blocks, connections, connections_meta, model_meta) :

	n = dict(zip(blocks, count()))

	struct = [ ((n[b0], t0.name), [ (n[b1], t1.name) for b1, t1 in vals ])
			for (b0, t0), vals in connections.iteritems() ]

	types = [ (nr, block.prototype.type_name) for block, nr in n.iteritems() ]

	conn_meta = [ ((n[b0], t0.name, n[b1], t1.name), v)
		for (b0, t0, b1, t1), v in connections_meta.iteritems() ]

	meta = (
		model_meta,
#		dict(map(lambda b: (n[b], dfs.BlockModel.get_meta(b), ), blocks)),
		{ n[b] : dfs.BlockModel.get_meta(b) for b in blocks },
		conn_meta
	)
	return types, struct, meta

# ------------------------------------------------------------------------------------------------------------

def restore_dfs_model(types, struct, meta) :
	m = dfs.GraphModel()
	m.enable_logging = False
	load_to_dfs_model(m, types, struct, meta, deserializing=True)
	m.enable_logging = True
	return m

# ------------------------------------------------------------------------------------------------------------

def load_to_dfs_model(m, types, struct, meta, deserializing=False) :

	if len(meta) == 2 :
		graph_meta, block_meta, = meta
		conn_meta = {} #TODO
	else :
		graph_meta, block_meta, cnm = meta
		conn_meta = dict(cnm)
		
	block_meta = dict(block_meta)#XXX XXX

	fact = dfs.create_block_factory()
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
	
		if isinstance(sb.prototype, dfs.JointProto) :
			st = dfs.Out("", dfs.C, 0)
			sb.terms.append(st)
		else :
			st = tuple(islice(dropwhile(lambda t: t.name != term_name, sb.terms), 0, 1))[0]

		for ntb, stt in conns :

			tb = blocks[ntb]

			if isinstance(tb.prototype, dfs.JointProto) :
				tt = dfs.In("", dfs.C, 0)
				tb.terms.append(tt)
			else :
				tt = tuple(islice(dropwhile(lambda t: t.name != stt, tb.terms), 0, 1))[0]
			
			meta = (conn_meta[(block_nr, term_name, ntb, stt)] 
				if (block_nr, term_name, ntb, stt) in conn_meta else {})
			
			conn_list.append((sb, st, tb, tt))
#			print "conn:", (sb, st, tb, tt)
			m.add_connection(sb, st, tb, tt, meta=meta, deserializing=deserializing)

#	print "conn_list:", conn_list
	return blocks.values(), conn_list

# ------------------------------------------------------------------------------------------------------------

