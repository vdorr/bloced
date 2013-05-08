
"""
general utilities
"""

import traceback
import signal
from functools import partial
import sys


def here(depth=1) :
	"""
	prints <depth> frames of call stack
	"""
	stack = traceback.extract_stack()[:-1]
	take = len(stack) if depth > len(stack)  else depth
	trace = stack[(len(stack)-take):]
	return "->".join([ "{0}:{1}".format(frame[2], frame[1]) for frame in trace ])


def sigterm_handler(signal, frame, callback=lambda : -1):
	rc = None
	if not callback is None :
		rc = callback()
	sys.exit(0 if rc is None else  rc)


def install_sigterm_handler(callback) :
	signal.signal(signal.SIGINT, partial(sigterm_handler,
		callback=callback))


