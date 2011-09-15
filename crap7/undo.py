
from dfs import GraphModelListener

# ------------------------------------------------------------------------------------------------------------

class __frame(object) :

	def __init__(self, changes, annotation) :
		pass

# ------------------------------------------------------------------------------------------------------------

class UndoListener(GraphModelListener) :

	# ---------------------------------------------------------------------

	def block_added(self, block) :
		self.__changed()

	def block_removed(self, block) :
		self.__changed()

	def block_changed(self, block, event=None) :
		self.__changed()

	def connection_added(self, sb, st, tb, tt, deserializing=False) :
		if not deserializing :
			self.__changed()

	def connection_removed(self, sb, st, tb, tt) :
		self.__changed()

	# ---------------------------------------------------------------------

	def can_undo(self, steps=1) :
		pass

	def can_redo(self, step=1) :
		pass

	def undo(self, steps=1) :
		pass

	def redo(self, step=1) :
		pass

	def clear(self) :
		pass

	def begin_edit(self, annotation="") :
		pass

	def end_edit(self, annotation=None) :
		pass

	# ---------------------------------------------------------------------

	def __changed(self) :
		self.__changed_flag = True

	def set_changed(self, v) :
		self.__changed_flag = v

	changed = property(lambda self: self.__changed_flag)

	def __init__(self, model, file_object, max_size) :
		self.__changed_flag = False

# ------------------------------------------------------------------------------------------------------------

