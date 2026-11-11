import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, UploadFile, File, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from fog_node import config, database, media, projects, resources, worker

app = FastAPI(title="FogEdit")

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.is_dir():
	app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.on_event("startup")
def _startup():
	database.init_db()


def _now():
	return datetime.now(timezone.utc).isoformat()


@app.get("/")
def index():
	index_path = STATIC_DIR / "index.html"
	if not index_path.exists():
		return JSONResponse({"detail": "Frontend not installed"}, status_code=404)
	return FileResponse(str(index_path))


@app.get("/health")
def health():
	return {"status": "ok"}


@app.get("/status")
def status():
	conn = database.get_connection()
	try:
		queue = conn.execute("SELECT COUNT(*) AS n FROM jobs WHERE status = 'QUEUED'").fetchone()["n"]
		active = conn.execute("SELECT COUNT(*) AS n FROM jobs WHERE status = 'PROCESSING'").fetchone()["n"]
		completed = conn.execute("SELECT COUNT(*) AS n FROM jobs WHERE status = 'COMPLETED'").fetchone()["n"]
		failed = conn.execute("SELECT COUNT(*) AS n FROM jobs WHERE status = 'FAILED'").fetchone()["n"]
	finally:
		conn.close()
	return {
		"nodeId": config.NODE_ID,
		"queue": queue,
		"active": active,
		"completed": completed,
		"failed": failed
	}


@app.get("/node/info")
def node_info():
	return resources.get_node_info()


@app.post("/projects")
async def create_project(request: Request):
	body = await request.json()
	name = (body or {}).get("name", "").strip()
	if not name:
		raise HTTPException(status_code=400, detail="Project name required")
	return projects.create_project(name)


@app.get("/projects")
def list_projects():
	return projects.list_projects()


@app.get("/projects/{project_id}")
def get_project(project_id: str):
	project = projects.get_project(project_id)
	if not project:
		raise HTTPException(status_code=404, detail="Project not found")
	return project


@app.post("/files")
async def upload_file(file: UploadFile = File(...), project_id: str = Form(None)):
	file_id = str(uuid.uuid4())
	dest = Path(config.UPLOAD_DIR) / (file_id + "_" + (file.filename or "upload.bin"))
	contents = await file.read()
	dest.write_bytes(contents)
	try:
		meta = media.probe_media(str(dest))
	except Exception as exc:
		try:
			dest.unlink()
		except OSError:
			pass
		raise HTTPException(status_code=400, detail="Invalid media: " + str(exc))
	conn = database.get_connection()
	try:
		conn.execute(
			"INSERT INTO files (id, project_id, original_name, stored_path, duration, format, created_at) "
			"VALUES (?, ?, ?, ?, ?, ?, ?)",
			(file_id, project_id, file.filename, str(dest),
			 meta.get("duration"), meta.get("format"), _now())
		)
		conn.commit()
	finally:
		conn.close()
	return {
		"id": file_id,
		"project_id": project_id,
		"original_name": file.filename,
		"duration": meta.get("duration"),
		"format": meta.get("format")
	}


@app.get("/files/{file_id}/content")
def file_content(file_id: str):
	conn = database.get_connection()
	try:
		row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
	finally:
		conn.close()
	if not row:
		raise HTTPException(status_code=404, detail="File not found")
	path = Path(row["stored_path"])
	if not path.exists():
		raise HTTPException(status_code=404, detail="File content missing")
	return FileResponse(str(path))


def _normalize_operations(body):
	ops = body.get("operations")
	if isinstance(ops, list) and ops:
		return ops
	if "start" in body and "end" in body:
		return [{"op": "trim", "start": body["start"], "end": body["end"]}]
	return []


def _validate_operations(ops):
	if not ops:
		raise HTTPException(status_code=400, detail="operations required")
	for op in ops:
		if not isinstance(op, dict) or "op" not in op:
			raise HTTPException(status_code=400, detail="Each operation needs an 'op' field")
		kind = op["op"]
		if kind not in media.SUPPORTED_OPS:
			raise HTTPException(status_code=501,
								detail="Operation not implemented: " + str(kind))
		if kind == "trim":
			s, e = op.get("start"), op.get("end")
			if s is None or e is None or float(s) < 0 or float(e) <= float(s):
				raise HTTPException(status_code=400, detail="Invalid trim parameters")
		if kind == "resize":
			w, h = op.get("width"), op.get("height")
			if not w or not h or int(w) <= 0 or int(h) <= 0:
				raise HTTPException(status_code=400, detail="Invalid resize parameters")

		if kind in media.EFFECT_OPS:
			try:
				media.validate_operation(op)
			except ValueError as exc:
				raise HTTPException(status_code=400,
									detail="Invalid " + kind + " parameters: " + str(exc))

@app.post("/jobs")
async def create_job(request: Request):
	body = await request.json()
	file_id = (body or {}).get("file_id")
	if not file_id:
		raise HTTPException(status_code=400, detail="file_id required")
	project_id = body.get("project_id")
	ops = _normalize_operations(body)
	_validate_operations(ops)

	conn = database.get_connection()
	try:
		frow = conn.execute("SELECT id, stored_path FROM files WHERE id = ?", (file_id,)).fetchone()
	finally:
		conn.close()
	if not frow:
		raise HTTPException(status_code=404, detail="File not found")

	effect_ops = [op["op"] for op in ops if op["op"] in media.EFFECT_OPS]
	if effect_ops and frow["stored_path"] and Path(frow["stored_path"]).exists():
		try:
			has_video = media.has_video_stream(frow["stored_path"])
		except ValueError as exc:
			raise HTTPException(status_code=400, detail="Invalid media: " + str(exc))
		if not has_video:
			raise HTTPException(status_code=400,
								detail="Operation '" + effect_ops[0] + "' requires a file with a video stream")
	job_id = str(uuid.uuid4())
	now = _now()
	conn = database.get_connection()
	try:
		conn.execute(
			"INSERT INTO jobs (id, file_id, project_id, status, operations, progress, "
			"current_step, step_index, total_steps, error, result_path, created_at, updated_at) "
			"VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
			(job_id, file_id, project_id, "QUEUED", json.dumps(ops),
			 0, None, 0, len(ops), None, None, now, now)
		)
		conn.commit()
	finally:
		conn.close()

	worker.start_job_async(job_id)
	return _job_response(job_id)


def _job_response(job_id):
	conn = database.get_connection()
	try:
		row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
	finally:
		conn.close()
	if not row:
		raise HTTPException(status_code=404, detail="Job not found")
	data = dict(row)
	try:
		data["operations"] = json.loads(data.get("operations") or "[]")
	except (ValueError, TypeError):
		data["operations"] = []
	return data


@app.get("/jobs")
def list_jobs(project_id: str = None):
	conn = database.get_connection()
	try:
		if project_id:
			rows = conn.execute(
				"SELECT * FROM jobs WHERE project_id = ? ORDER BY created_at DESC",
				(project_id,)
			).fetchall()
		else:
			rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC").fetchall()
	finally:
		conn.close()
	result = []
	for r in rows:
		d = dict(r)
		try:
			d["operations"] = json.loads(d.get("operations") or "[]")
		except (ValueError, TypeError):
			d["operations"] = []
		result.append(d)
	return result


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
	return _job_response(job_id)


@app.get("/results/{job_id}")
def get_result(job_id: str):
	conn = database.get_connection()
	try:
		row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
	finally:
		conn.close()
	if not row:
		raise HTTPException(status_code=404, detail="Job not found")
	if row["status"] != "COMPLETED" or not row["result_path"]:
		raise HTTPException(status_code=404, detail="Result not ready")
	path = Path(row["result_path"])
	if not path.exists():
		raise HTTPException(status_code=404, detail="Result file missing")
	return FileResponse(str(path), filename=str(job_id) + ".mp4")
