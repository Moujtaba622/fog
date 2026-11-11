import io
from pathlib import Path

import httpx
from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from scheduler import config, proxy, round_robin

app = FastAPI(title="FogEdit Scheduler (prototype)")

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.is_dir():
	app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def index():
	index_path = STATIC_DIR / "index.html"
	if not index_path.exists():
		return JSONResponse({"detail": "Scheduler UI not installed"}, status_code=404)
	return FileResponse(str(index_path))


@app.get("/health")
def health():
	return {"status": "ok"}


@app.get("/nodes")
async def nodes_status():
	results = []
	for url in config.NODES:
		entry = {"url": url, "reachable": False, "info": None, "error": None}
		try:
			info = await proxy.get_json(url + "/node/info")
			entry["reachable"] = True
			entry["info"] = info
		except Exception as exc:
			entry["error"] = str(exc)
		results.append(entry)
	return {"nodes": results, "next_index": round_robin.current_index()}


@app.post("/submit-file")
async def submit_file(file: UploadFile = File(...), project_id: str = Form(None)):
	target = round_robin.pick_node()
	contents = await file.read()
	files = {"file": (file.filename or "upload.bin", io.BytesIO(contents), file.content_type or "application/octet-stream")}
	data = {}
	if project_id:
		data["project_id"] = project_id
	try:
		result = await proxy.forward_multipart(target + "/files", files, data)
	except httpx.HTTPStatusError as exc:
		raise HTTPException(status_code=exc.response.status_code,
							detail="Node rejected upload: " + exc.response.text[:300])
	except Exception as exc:
		raise HTTPException(status_code=502, detail="Node unreachable: " + str(exc))
	result["assigned_node"] = target
	return result


@app.post("/submit-job")
async def submit_job(request: Request):
	body = await request.json()
	target = round_robin.pick_node()
	try:
		result = await proxy.forward_json(target + "/jobs", body)
	except httpx.HTTPStatusError as exc:
		raise HTTPException(status_code=exc.response.status_code,
							detail="Node rejected job: " + exc.response.text[:300])
	except Exception as exc:
		raise HTTPException(status_code=502, detail="Node unreachable: " + str(exc))
	result["assigned_node"] = target
	return result


@app.get("/job/{node_url:path}/{job_id}")
async def get_job(node_url: str, job_id: str):
	url = node_url.rstrip("/") + "/jobs/" + job_id
	try:
		return await proxy.get_json(url)
	except httpx.HTTPStatusError as exc:
		raise HTTPException(status_code=exc.response.status_code, detail=exc.response.text[:300])
	except Exception as exc:
		raise HTTPException(status_code=502, detail="Node unreachable: " + str(exc))


@app.get("/result/{node_url:path}/{job_id}")
async def get_result(node_url: str, job_id: str):
	url = node_url.rstrip("/") + "/results/" + job_id

	async def gen():
		async for chunk in proxy.stream_file(url):
			yield chunk

	try:
		return StreamingResponse(gen(), media_type="video/mp4",
								 headers={"Content-Disposition": "attachment; filename=" + job_id + ".mp4"})
	except Exception as exc:
		raise HTTPException(status_code=502, detail="Node unreachable: " + str(exc))
