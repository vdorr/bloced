
"""
general utilities
"""

import traceback

def here(depth=1) :
	"""
	prints <depth> frames of call stack
	"""
	stack = traceback.extract_stack()[:-1]
	take = len(stack) if depth > len(stack)  else depth
	trace = stack[(len(stack)-take):]
	return "->".join([ "{0}:{1}".format(frame[2], frame[1]) for frame in trace ])

