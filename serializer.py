
"""
module for serialization and deserialization of GraphModel and Workbench objects
"""

import pickle
from itertools import count, dropwhile, islice
import dfs
import core
from pprint import pprint
from utils import here
from collections import OrderedDict

# ------------------------------------------------------------------------------------------------------------

def pickle_dfs_model(m, f) :
	"""
	convert GraphModel m to serializable form, pickle and dump it into file-like object f
	"""
	try :
		pickle.dump(get_dfs_model_data(m), f, 0)
	except pickle.PickleError :
		print("PickleError")
		raise


def unpickle_dfs_model(f, lib=None) :
	"""
	read pickled serialized GraphModel from file-like object f,
	if non None recover using block factory lib and return as new instance
	"""
	try :
		types, struct, meta = pickle.load(f)
#		pprint((types, struct, meta))
		return restore_dfs_model(types, struct, meta, lib)
	except pickle.PickleError :
		print("PickleError")
		raise

# ------------------------------------------------------------------------------------------------------------

#TODO for use with clipboard and undo pass blocks and other components separately
#TODO move to dfs.py?
def get_dfs_model_data(m) :
	"""
	convenience wrapper around get_dfs_model_data2
	"""
	return get_dfs_model_data2(m.blocks, m.connections, m.connections_meta, dfs.GraphModel.get_meta(m))

# ------------------------------------------------------------------------------------------------------------

def __term_nfo(t0) :
	return (t0[0].name, t0[1]) if isinstance(t0, tuple) else t0.name


def __get_block_full_type(block) :
#	print here(), block.prototype.library, block.prototype.type_name
	full_type = block.prototype.type_name
	if not block.prototype.library is None :
		full_type = block.prototype.library + "." + full_type
	return full_type


def get_dfs_model_data2(blocks, connections, connections_meta, model_meta) :
	"""
	convert content of GraphModel to tuple (types, struct, meta) of simple, serializable types
	types - list of tuples (block_number, type_name)
	struct - list of tuples (src_block_term_info, [dst_block_term_info, ...])
		where block_term_info is tuple (block_number, term_name)
		or (block_number, (term_name, term_number)) if block terminal is variadic
	meta - tuple (model_meta, block_meta_dict, conn_meta)
		where model_meta is basically unused, block_meta_dict is dict
		{block_number:{block_meta_key:block_meta_value, ...}, ...}
		conn_meta is list of tuples
		((src_block_number, src_block_term_info, dst_block_number, dst_block_term_info), {meta_key:meta_value, ...})
	"""

	n = OrderedDict(zip(blocks, count()))

	struct = [ ((n[b0], __term_nfo(t0)), [ (n[b1], __term_nfo(t1)) for b1, t1 in vals ])
			for (b0, t0), vals in connections.items() ]

	types = [ (nr, __get_block_full_type(block)) for block, nr in n.items() ]

	conn_meta = [ ((n[b0], __term_nfo(t0), n[b1], __term_nfo(t1)), v)
		for (b0, t0, b1, t1), v in connections_meta.items() ]

	meta = (
		model_meta,
		OrderedDict((n[b], dfs.BlockModel.get_meta(b)) for b in blocks),
		conn_meta
	)
	return types, struct, meta

# ------------------------------------------------------------------------------------------------------------

def restore_dfs_model(types, struct, meta, lib, use_cached_proto=True) :
	m = dfs.GraphModel()
	m.enable_logging = False
	fact = core.create_block_factory() if lib is None else lib
	load_to_dfs_model(m, types, struct, meta, fact, deserializing=True,
		use_cached_proto=use_cached_proto)
	m.enable_logging = True
	return m

# ------------------------------------------------------------------------------------------------------------

def __stname(t0) :
	return t0[0] if isinstance(t0, tuple) else t0


def load_to_dfs_model(m, types, struct, meta, fact,
		deserializing=False,#TODO rename
		use_cached_proto=True) :
	"""
	load deserialized types, struct, meta into supplied GraphModel instance
	model is restored using block factory fact
	deserializing is passed to some GraphModel methods to distinguish
	change from user action and desrialization
	"""

	if len(meta) == 2 :
		graph_meta, block_meta, = meta
		conn_meta = {} #TODO
	else :
		graph_meta, block_meta, cnm = meta
		conn_meta = dict(cnm)
		
	block_meta = dict(block_meta)#XXX XXX

	blocks = {}
	for n, type_name in types :
		new_block_meta = block_meta[n]
#		print here(), use_cached_proto, new_block_meta
		if ( use_cached_proto and not new_block_meta is None and
			"cached_prototype" in new_block_meta ) :
			bp = new_block_meta.pop("cached_prototype")
			t = core.block_proto_from_proto_data(bp)
#			print here()
		else :
			t = fact.get_block_by_name(type_name)
		b = dfs.BlockModel(t, m)
		b.set_meta({} if new_block_meta is None else new_block_meta)
		blocks[n] = b
		m.add_block(b)

	conn_list = []
	for (block_nr, term_name), conns in struct :
		sb = blocks[block_nr]

		t_name = __stname(term_name)
		st, = tuple(islice(dropwhile(lambda t: t.name != t_name, sb.terms), 0, 1))

		if isinstance(term_name, tuple) :
			st = (st, term_name[1])

		for ntb, stt in conns :

			tb = blocks[ntb]

			stt_name = __stname(stt)
			tt, = tuple(islice(dropwhile(lambda t: t.name != stt_name, tb.terms), 0, 1))
			
			meta = (conn_meta[(block_nr, term_name, ntb, stt)] 
				if (block_nr, term_name, ntb, stt) in conn_meta else {})

			tt2 = (tt, stt[1]) if isinstance(stt, tuple) else tt #XXX check this if problem with varterm occurs!
#			print(here(), sb, st, tb, tt2, meta, deserializing)

			m.add_connection(sb, st, tb, tt2, meta=meta, deserializing=deserializing)

			conn_list.append((sb, st, tb, tt2))

	return blocks.values(), conn_list


CONTAINER_VERSION = (0, 0, 1)
RES_TYPE_SHEET = "sheet"
RES_TYPE_SHEET_VERSION = (0, 0, 1)


def pickle_workbench(wrk, f) :
	"""
	convert Workbench wrk to serializable form, pickle and dump it into file-like object f
	"""
	try :
		pickle.dump(get_workbench_data(wrk), f, 0)
	except pickle.PickleError :
		print("PickleError")
		raise


def get_workbench_data(w) :
	"""
	convert content of Workbench to simple, serializable types
	"""
	meta = w.get_meta()
	resources = []
	for sheet_name in sorted(w.sheets.keys()) :
		sheet = w.sheets[sheet_name]
		s = get_dfs_model_data(sheet)
#		print here(), s
		resources.append((RES_TYPE_SHEET, RES_TYPE_SHEET_VERSION, sheet_name, s))
	x = (CONTAINER_VERSION, meta, tuple(resources))
#	print x
	return x


def unpickle_workbench(f, w, use_cached_proto=True) :
	"""
	read pickled serialized Workbench data from file-like object f,
	and load it into supplied Workbench instance w
	"""
	try :
		version, meta, resources = unpickle_workbench_data(f)
	except Exception as e :
		return (False, "load_error", e)

	return restore_workbench((version, meta, resources), w, use_cached_proto=use_cached_proto)


def get_resource(data, res_type, res_version, res_name) :
	"""
	return iterator with resources of given type name and version
	"""
	version, _, resources = data
	if not check_w_data_legality(data) :
		raise Exception("container_version_mismatch")
	for r_type, r_version, r_name, resrc in resources :
		if ((res_type is None or r_type == res_type) and
		    (res_version is None or r_version == res_version) and
		    (res_name is None or r_name == res_name)) :
			yield resrc


def check_resource_legality(data, resource) :
	"""
	check if resource has valid type and version
	"""
#TODO
	pass


def check_w_data_legality(data) :
	version, _, _ = data
	return version == CONTAINER_VERSION #XXX lower than or equal ?


#TODO this is not the right place for method like this
def restore_workbench(data, w, use_cached_proto=True) :
	"""
	load data into supplied Workbench instance w
	"""

	version, meta, resources = data

	w.set_meta(meta)

	for r_type, r_version, r_name, resrc in resources :
		if r_type == RES_TYPE_SHEET :
			if r_version == RES_TYPE_SHEET_VERSION :
				types, struct, meta = resrc
#				pprint((types, struct, meta))
				m = restore_dfs_model(types, struct, meta, w.blockfactory,
					use_cached_proto=use_cached_proto)
				w.add_sheet(sheet=m, name=r_name)
			else :
				pass
		else :
			pass

	return (True, "ok", w)



def unpickle_workbench_data(f) :
	"""
	return tuple (version, meta, resources) of Workbench data read from pickle file-like object f
	resources is tuple of tuples (r_type, r_version, r_name, resrc) where r_type is constant RES_TYPE_*
	raises Exception if something fails (unpickling or container version check)
	"""
	version, meta, resources = pickle.load(f)
	if not check_w_data_legality((version, meta, resources)) :
		raise Exception("container_version_mismatch")
	return version, meta, resources


