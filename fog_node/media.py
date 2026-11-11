import json
import subprocess
from fog_node import effects

def probe_media(path):
	cmd = [
		"ffprobe", "-v", "error", "-print_format", "json",
		"-show_format", "-show_streams", str(path),
	]
	proc = subprocess.run(cmd, capture_output=True, text=True)
	if proc.returncode != 0:
		raise ValueError("ffprobe failed: " + proc.stderr[-300:])
	data = json.loads(proc.stdout or "{}")
	fmt = data.get("format", {})
	duration = fmt.get("duration")
	try:
		duration = float(duration) if duration is not None else None
	except (TypeError, ValueError):
		duration = None
	format_name = fmt.get("format_name")
	return {"duration": duration, "format": format_name}

def has_video_stream(path):
	cmd = ["ffprobe", "-v", "error", "-print_format", "json",
		   "-show_streams", "-select_streams", "v", str(path)]
	proc = subprocess.run(cmd, capture_output=True, text=True)
	if proc.returncode != 0:
		raise ValueError("ffprobe failed: " + proc.stderr[-300:])
	streams = json.loads(proc.stdout or "{}").get("streams", [])
	return any(not s.get("disposition", {}).get("attached_pic") for s in streams)

def build_trim(start, end):
	return ["-ss", str(start), "-to", str(end)]


def build_resize(width, height):
	return ["-vf", "scale=" + str(width) + ":" + str(height)]


def build_compress(crf=23, preset="medium"):
	return ["-crf", str(crf), "-preset", preset]


def build_convert(fmt="mp4"):
	return ["-f", fmt]


SUPPORTED_OPS = {"trim", "resize", "compress", "convert", "denoise", "color_grade"}
EFFECT_OPS = {"denoise", "color_grade"}


def validate_operation(op):
	kind = op.get("op")
	if kind == "denoise":
		effects.normalize_denoise(op)
	elif kind == "color_grade":
		effects.normalize_color_grade(op)


def build_step_args(op):
	kind = op.get("op")
	if kind == "trim":
		return build_trim(op["start"], op["end"])
	if kind == "resize":
		return build_resize(op["width"], op["height"])
	if kind == "compress":
		return build_compress(op.get("crf", 23), op.get("preset", "medium"))
	if kind == "convert":
		return build_convert(op.get("format", "mp4"))
	if kind == "denoise":
		return effects.build_denoise(op)
	if kind == "color_grade":
		return effects.build_color_grade(op)
	
	raise ValueError("Unsupported operation: " + str(kind))
