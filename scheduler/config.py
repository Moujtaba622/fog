import os


def _parse_nodes():
	raw = os.environ.get("FOGEDIT_NODES")
	if raw:
		return [u.strip().rstrip("/") for u in raw.split(",") if u.strip()]
	return [
		os.environ.get("FOGEDIT_NODE_1", "http://127.0.0.1:8001"),
		os.environ.get("FOGEDIT_NODE_2", "http://127.0.0.1:8002"),
		os.environ.get("FOGEDIT_NODE_3", "http://127.0.0.1:8003"),
	]


NODES = _parse_nodes()

SCHEDULER_PORT = int(os.environ.get("FOGEDIT_SCHEDULER_PORT", "9000"))
