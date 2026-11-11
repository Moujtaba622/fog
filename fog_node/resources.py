import os
import shutil
import time
from datetime import datetime, timezone

import psutil

from fog_node import config, database


def _db_path():
	return config.DB_PATH


def _data_dir():
	return config.DATA_DIR


def count_jobs_by_status(status):
	conn = database.get_connection()
	try:
		row = conn.execute(
			"SELECT COUNT(*) AS n FROM jobs WHERE status = ?", (status,)
		).fetchone()
		return row["n"] if row else 0
	finally:
		conn.close()


def get_node_info():
	cpu = psutil.cpu_percent(interval=None)
	mem = psutil.virtual_memory().percent
	try:
		usage = shutil.disk_usage(_data_dir())
		available_gb = round(usage.free / (1024 ** 3), 2)
	except OSError:
		available_gb = 0.0
	queue_size = count_jobs_by_status("QUEUED")
	active_jobs = count_jobs_by_status("PROCESSING")
	if queue_size == 0 and active_jobs == 0:
		status = "AVAILABLE"
	elif active_jobs > 0:
		status = "BUSY"
	else:
		status = "AVAILABLE"
	return {
		"nodeId": config.NODE_ID,
		"status": status,
		"cpuUsage": round(cpu, 1),
		"memoryUsage": round(mem, 1),
		"queueSize": queue_size,
		"activeJobs": active_jobs,
		"availableStorage": available_gb,
		"timestamp": datetime.now(timezone.utc).isoformat()
	}
