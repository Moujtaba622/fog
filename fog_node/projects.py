import uuid
from datetime import datetime, timezone

from fog_node import database


def _now():
	return datetime.now(timezone.utc).isoformat()


def create_project(name):
	project_id = str(uuid.uuid4())
	now = _now()
	conn = database.get_connection()
	try:
		conn.execute(
			"INSERT INTO projects (id, name, created_at, updated_at) VALUES (?, ?, ?, ?)",
			(project_id, name, now, now)
		)
		conn.commit()
	finally:
		conn.close()
	return get_project(project_id)


def list_projects():
	conn = database.get_connection()
	try:
		rows = conn.execute(
			"SELECT id, name, created_at, updated_at FROM projects ORDER BY created_at DESC"
		).fetchall()
		return [dict(r) for r in rows]
	finally:
		conn.close()


def get_project(project_id):
	conn = database.get_connection()
	try:
		row = conn.execute(
			"SELECT id, name, created_at, updated_at FROM projects WHERE id = ?",
			(project_id,)
		).fetchone()
		if not row:
			return None
		project = dict(row)
		files = conn.execute(
			"SELECT * FROM files WHERE project_id = ? ORDER BY created_at DESC",
			(project_id,)
		).fetchall()
		jobs = conn.execute(
			"SELECT * FROM jobs WHERE project_id = ? ORDER BY created_at DESC",
			(project_id,)
		).fetchall()
		project["files"] = [dict(f) for f in files]
		project["jobs"] = [dict(j) for j in jobs]
		return project
	finally:
		conn.close()
