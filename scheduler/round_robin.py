import threading

from scheduler import config


_lock = threading.Lock()
_next_index = 0


def pick_node():
	global _next_index
	with _lock:
		node = config.NODES[_next_index % len(config.NODES)]
		_next_index = (_next_index + 1) % len(config.NODES)
		return node


def current_index():
	with _lock:
		return _next_index
