# FogEdit — Milestone 1: Fog Node

## Purpose

This milestone implements one independently runnable fog node. It accepts video uploads, stores file metadata, queues trim jobs, processes them with FFmpeg, and exposes job status and downloadable results through a REST API.

This is a single-node foundation. It does not yet implement a central coordinator, distributed scheduling, node-to-node communication, authentication, or a web interface.

## Requirements

- Python 3.11 or newer
- FFmpeg and FFprobe installed and available on `PATH`
- A writable directory for local data

Verify the media tools before starting:

	ffmpeg -version
	ffprobe -version

## Install

Create and activate a virtual environment.

Windows PowerShell:

	py -3.11 -m venv .venv
	.\.venv\Scripts\Activate.ps1
	python -m pip install --upgrade pip
	pip install -r requirements.txt

Linux:

	python3 -m venv .venv
	source .venv/bin/activate
	python -m pip install --upgrade pip
	pip install -r requirements.txt

## Configuration

Configuration is provided through environment variables.

| Variable | Default | Meaning |
| --- | --- | --- |
| NODE_ID | fog-1 | Identifier reported by this node |
| PORT | 8000 | Port for the API server |
| DATA_DIR | data | Root directory for the database and media files |

The data directory contains:

- `fogedit.db` — SQLite metadata and persistent job queue
- `uploads/` — uploaded source files
- `results/` — completed output files
- `temp/` — temporary processing files

The upload endpoint currently enforces a 500 MiB limit per file.

## Run

From the repository root:

	python -m uvicorn main:app --host 127.0.0.1 --port 8000

Open the interactive API documentation at `http://127.0.0.1:8000/docs`.

To allow access from other machines on a trusted network, bind to `0.0.0.0` and configure suitable firewall rules. This milestone does not include authentication; do not expose it directly to an untrusted network.

## API workflow

### 1. Check health

	curl http://127.0.0.1:8000/health

### 2. Upload a video

	curl -X POST http://127.0.0.1:8000/files -F "file=@sample.mp4"

The response includes `file_id`, duration, size, and detected format. Keep the returned `file_id` for the next request.

### 3. Create a trim job

Replace `FILE_ID` with the identifier returned by the upload request. Times are seconds from the beginning of the source video.

	curl -X POST http://127.0.0.1:8000/jobs -H "Content-Type: application/json" -d "{\"file_id\":\"FILE_ID\",\"start_seconds\":5,\"end_seconds\":15}"

A successful response returns HTTP 202 and a `job_id`.

### 4. Poll job status

	curl http://127.0.0.1:8000/jobs/JOB_ID

Poll until `status` is `COMPLETED` or `FAILED`. The response includes queue wait time, processing time, input/output sizes, and a result URL when successful.

### 5. Download the result

	curl -L http://127.0.0.1:8000/results/JOB_ID --output trimmed.mp4

### 6. Inspect node status

	curl http://127.0.0.1:8000/status

The status endpoint reports the queued job count, active job, node ID, and local disk usage.

## Job lifecycle

	QUEUED -> PROCESSING -> COMPLETED
						 -> FAILED

The queue is stored in SQLite, so queued jobs survive application restarts. Jobs found in `PROCESSING` during startup are returned to `QUEUED`, allowing interrupted work to be retried.

Only one worker processes jobs at a time in this milestone. Processing time and queue wait time are stored separately.

## Current processing behavior

The first supported operation is video trimming. FFmpeg re-encodes video to H.264 and audio to AAC in an MP4 container. The implementation uses argument lists rather than shell command strings.

The node validates uploaded media with FFprobe, checks requested time boundaries, writes output to a temporary file, validates the result, and atomically moves it into the results directory before marking the job complete.

## Limitations

- One node and one worker only.
- Only the `TRIM` job type is supported.
- Uploads are limited to 500 MiB.
- Authentication, authorization, TLS, quotas, distributed coordination, and a user interface are not implemented.
- A single SQLite database is intended for this milestone, not high-throughput multi-node coordination.
- Production deployment requires authentication, resource limits, retention policies, and network security controls.

## Milestone 1 completion criteria

- The application starts and initializes its SQLite database.
- The health endpoint responds.
- A valid video can be uploaded and registered.
- A trim job is persisted and queued.
- The worker processes queued jobs and stores timing and size metrics.
- Job status can be queried.
- Completed output can be downloaded.
- Failed jobs expose an error message without returning a Python traceback.