import os


NODES = [
	os.environ.get("FOGEDIT_NODE_1", "http://127.0.0.1:8001"),
	os.environ.get("FOGEDIT_NODE_2", "http://127.0.0.1:8002"),
	os.environ.get("FOGEDIT_NODE_3", "http://127.0.0.1:8003"),
]

SCHEDULER_PORT = int(os.environ.get("FOGEDIT_SCHEDULER_PORT", "9000"))
