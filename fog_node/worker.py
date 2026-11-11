import json
import shutil
import subprocess
import threading
from datetime import datetime, timezone
from pathlib import Path

from fog_node import config, database, media


def _now():
	return datetime.now(timezone.utc).isoformat()


def _update_job(job_id, **fields):
	if not fields:
		return
	fields["updated_at"] = _now()
	cols = ", ".join(k + " = ?" for k in fields.keys())
	values = list(fields.values()) + [job_id]
	conn = database.get_connection()
	try:
		conn.execute("UPDATE jobs SET " + cols + " WHERE id = ?", values)
		conn.commit()
	finally:
		conn.close()


def _get_job(job_id):
	conn = database.get_connection()
	try:
		row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
		return dict(row) if row else None
	finally:
		conn.close()


def process_job(job_id):
	job = _get_job(job_id)
	if not job:
		return
	try:
		operations = json.loads(job.get("operations") or "[]")
	except (ValueError, TypeError):
		operations = []
	if not operations:
		_update_job(job_id, status="FAILED", error="No operations in job")
		return

	source = None
	conn = database.get_connection()
	try:
		frow = conn.execute("SELECT stored_path FROM files WHERE id = ?", (job["file_id"],)).fetchone()
	finally:
		conn.close()
	if frow and frow["stored_path"]:
		source = Path(frow["stored_path"])
	if not source or not source.exists():
		_update_job(job_id, status="FAILED", error="Source file missing")
		return

	temp_dir = Path(config.TEMP_DIR) / str(job_id)
	temp_dir.mkdir(parents=True, exist_ok=True)
	total = len(operations)
	_update_job(job_id, status="PROCESSING", progress=0, step_index=0, total_steps=total)

	current_input = source
	for idx, op in enumerate(operations):
		kind = op.get("op", "?")
		step_index = idx + 1
		_update_job(job_id, current_step=kind, step_index=step_index,
					progress=int(idx / total * 100))
		if kind not in media.SUPPORTED_OPS:
			_update_job(job_id, status="FAILED",
						error="Unsupported operation: " + kind + " (501)")
			return
		step_out = temp_dir / ("step_" + str(step_index) + ".mp4")
		try:
			args = media.build_step_args(op)
		except ValueError as exc:
			_update_job(job_id, status="FAILED", error=str(exc))
			return
		cmd = ["ffmpeg", "-y", "-i", str(current_input)] + args + [str(step_out)]
		proc = subprocess.run(cmd, capture_output=True, text=True)
		if proc.returncode != 0:
			_update_job(job_id, status="FAILED",
						error="FFmpeg failed at step " + str(step_index) + ": " + proc.stderr[-500:])
			return
		current_input = step_out

	result_path = Path(config.RESULT_DIR) / (str(job_id) + ".mp4")
	try:
		if current_input != result_path:
			shutil.copyfile(str(current_input), str(result_path))
	except OSError as exc:
		_update_job(job_id, status="FAILED", error="Failed to store result: " + str(exc))
		return
	_update_job(job_id, status="COMPLETED", progress=100, current_step=None,
				step_index=total, total_steps=total, result_path=str(result_path))


def start_job_async(job_id):
	t = threading.Thread(target=process_job, args=(job_id,), daemon=True)
	t.start()
