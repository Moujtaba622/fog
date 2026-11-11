import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("FOGEDIT_DATA_DIR", str(BASE_DIR / "data")))
UPLOAD_DIR = DATA_DIR / "uploads"
RESULT_DIR = DATA_DIR / "results"
TEMP_DIR = DATA_DIR / "temp"
DB_PATH = Path(os.environ.get("FOGEDIT_DB_PATH", str(DATA_DIR / "fogedit.db")))

NODE_ID = os.environ.get("FOGEDIT_NODE_ID", "fog-1")

for _dir in (DATA_DIR, UPLOAD_DIR, RESULT_DIR, TEMP_DIR):
	_dir.mkdir(parents=True, exist_ok=True)
