
import pickle
from itertools import count, dropwhile, islice
import dfs
import core
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
#		pprint((types, struct, meta))
		return restore_dfs_model(types, struct, meta)
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

#	print "get_dfs_model_data2(1):", connections

	n = dict(zip(blocks, count()))

	struct = [ ((n[b0], term_nfo(t0)), [ (n[b1], term_nfo(t1)) for b1, t1 in vals ])
			for (b0, t0), vals in connections.items() ]

#	print "get_dfs_model_data2: connections=", connections
#	print "get_dfs_model_data2: struct=", struct

	types = [ (nr, block.prototype.type_name) for block, nr in n.iteritems() ]

	conn_meta = [ ((n[b0], term_nfo(t0), n[b1], term_nfo(t1)), v)
		for (b0, t0, b1, t1), v in connections_meta.items() ]

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

def stname(t0) :
	return t0[0] if isinstance(t0, tuple) else t0

def load_to_dfs_model(m, types, struct, meta, deserializing=False) :

#	print "load_to_dfs_model(1):", types
#	print "load_to_dfs_model: struct=", struct
#	print "load_to_dfs_model(3):", meta

	if len(meta) == 2 :
		graph_meta, block_meta, = meta
		conn_meta = {} #TODO
	else :
		graph_meta, block_meta, cnm = meta
		conn_meta = dict(cnm)
		
	block_meta = dict(block_meta)#XXX XXX

	fact = core.create_block_factory()#XXX XXX
	blocks = {}
	for n, type_name in types :
		t = fact.get_block_by_name(type_name)
		b = dfs.BlockModel(t, m)
		b.set_meta(block_meta[n])
		blocks[n] = b
		m.add_block(b)

#	pprint(blocks)

#	conn_list = []
	for (block_nr, term_name), conns in struct :
		sb = blocks[block_nr]
	
#		if isinstance(sb.prototype, core.JointProto) :
#			st = dfs.Out(0, "", dfs.C, 0)
#			sb.terms.append(st)
#		else :
#		if True :
		t_name = stname(term_name)
		st, = tuple(islice(dropwhile(lambda t: t.name != t_name, sb.terms), 0, 1))

		if isinstance(term_name, tuple) :
			st = (st, term_name[1])
#		print "term_name=", term_name, "st=", st

#		print (block_nr, term_name), conns
		for ntb, stt in conns :

#			print "load_to_dfs_model(4):", ntb, stt

			tb = blocks[ntb]

#			print "ntb, stt:", ntb, "'", stt, "'"

#			print "666: ", stt
#			if isinstance(tb.prototype, core.JointProto) :
#				tt = dfs.In(0, "", dfs.C, 0)
##				assert(len(tb.inputs) == 0)
#				tb.terms.append(tt)
#				print ntb, stt, [ (tx.name, tx.direction) for tx in tb.terms ]
#			else :
#			if True :
			stt_name = stname(stt)
			tt, = tuple(islice(dropwhile(lambda t: t.name != stt_name, tb.terms), 0, 1))
			
			meta = (conn_meta[(block_nr, term_name, ntb, stt)] 
				if (block_nr, term_name, ntb, stt) in conn_meta else {})

#			if isinstance(term_name, tuple) :
#				st = (st, term_name[1])
#			print "stt=", stt, "tt=", tt

			m.add_connection(sb, st, tb, (tt, stt[1]) if isinstance(stt, tuple) else tt,#XXX check this if problem with varterm occurs!
				meta=meta, deserializing=deserializing)

#			conn_list.append((sb, st, tb, tt))
#			print "load_to_dfs_model:", (sb, st, tb, tt)
#			m.add_connection(sb, st, tb, tt, meta=meta, deserializing=deserializing)

#	print "load_to_dfs_model(5):", m.connections

#	print "conn_list:", conn_list
#	return blocks.values(), conn_list

# ------------------------------------------------------------------------------------------------------------

