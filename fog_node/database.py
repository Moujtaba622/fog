import sqlite3

from fog_node import config


def get_connection():
	conn = sqlite3.connect(str(config.DB_PATH))
	conn.row_factory = sqlite3.Row
	return conn


def init_db():
	conn = get_connection()
	try:
		conn.executescript(
			"""
			CREATE TABLE IF NOT EXISTS projects (
				id TEXT PRIMARY KEY,
				name TEXT NOT NULL,
				created_at TEXT NOT NULL,
				updated_at TEXT NOT NULL
			);

			CREATE TABLE IF NOT EXISTS files (
				id TEXT PRIMARY KEY,
				project_id TEXT,
				original_name TEXT,
				stored_path TEXT,
				duration REAL,
				format TEXT,
				created_at TEXT NOT NULL
			);

			CREATE TABLE IF NOT EXISTS jobs (
				id TEXT PRIMARY KEY,
				file_id TEXT NOT NULL,
				project_id TEXT,
				status TEXT NOT NULL,
				operations TEXT,
				progress INTEGER DEFAULT 0,
				current_step TEXT,
				step_index INTEGER DEFAULT 0,
				total_steps INTEGER DEFAULT 0,
				error TEXT,
				result_path TEXT,
				created_at TEXT NOT NULL,
				updated_at TEXT NOT NULL
			);
			"""
		)
		_migrate(conn)
		conn.commit()
	finally:
		conn.close()


def _migrate(conn):
	_add_column_if_missing(conn, "files", "project_id", "TEXT")
	_add_column_if_missing(conn, "jobs", "project_id", "TEXT")
	_add_column_if_missing(conn, "jobs", "operations", "TEXT")
	_add_column_if_missing(conn, "jobs", "progress", "INTEGER DEFAULT 0")
	_add_column_if_missing(conn, "jobs", "current_step", "TEXT")
	_add_column_if_missing(conn, "jobs", "step_index", "INTEGER DEFAULT 0")
	_add_column_if_missing(conn, "jobs", "total_steps", "INTEGER DEFAULT 0")
	_add_column_if_missing(conn, "jobs", "error", "TEXT")


def _add_column_if_missing(conn, table, column, decl):
	existing = [r["name"] for r in conn.execute("PRAGMA table_info(" + table + ")").fetchall()]
	if column not in existing:
		conn.execute("ALTER TABLE " + table + " ADD COLUMN " + column + " " + decl)
