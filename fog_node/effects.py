import math

ENCODE_ARGS = [
	"-c:v", "libx264", "-preset", "medium", "-crf", "18",
	"-pix_fmt", "yuv420p", "-movflags", "+faststart",
]


def _fmt(value):
	return "%g" % round(float(value), 4)


def _number(op, key, lo, hi, default):
	if key not in op or op[key] is None:
		return float(default)
	value = op[key]
	if isinstance(value, bool):
		raise ValueError("'" + key + "' must be a number")
	try:
		value = float(value)
	except (TypeError, ValueError):
		raise ValueError("'" + key + "' must be a number")
	if not math.isfinite(value) or value < lo or value > hi:
		raise ValueError("'" + key + "' must be between " + _fmt(lo) + " and " + _fmt(hi))
	return value


def _odd_int(op, key, lo, hi, default):
	value = _number(op, key, lo, hi, default)
	if value != int(value) or int(value) % 2 == 0:
		raise ValueError("'" + key + "' must be an odd integer")
	return int(value)


def _reject_unknown(op, allowed, what):
	extra = sorted(str(k) for k in set(op.keys()) - set(allowed))
	if extra:
		raise ValueError("unknown " + what + " parameter(s): " + ", ".join(extra))


# ---------------------------------------------------------------- denoise

DENOISE_METHODS = ("nlmeans", "hqdn3d")
DENOISE_INTENSITIES = ("light", "medium", "strong")
HQDN3D_KEYS = ("luma_spatial", "chroma_spatial", "luma_temporal", "chroma_temporal")
HQDN3D_PRESETS = {
	"light": (2.0, 1.5, 3.0, 2.25),
	"medium": (4.0, 3.0, 6.0, 4.5),
	"strong": (8.0, 6.0, 12.0, 9.0),
}
NLMEANS_PRESETS = {
	"light": {"strength": 2.0, "patch": 5, "research": 11},
	"medium": {"strength": 4.0, "patch": 7, "research": 15},
	"strong": {"strength": 8.0, "patch": 7, "research": 21},
}


def normalize_denoise(op):
	method = op.get("method", "nlmeans")
	if method not in DENOISE_METHODS:
		raise ValueError("method must be one of: " + ", ".join(DENOISE_METHODS))
	intensity = op.get("intensity", "medium")
	if intensity not in DENOISE_INTENSITIES:
		raise ValueError("intensity must be one of: " + ", ".join(DENOISE_INTENSITIES))
	if method == "hqdn3d":
		_reject_unknown(op, ("op", "method", "intensity") + HQDN3D_KEYS, "denoise")
		base = HQDN3D_PRESETS[intensity]
		params = {k: _number(op, k, 0, 30, base[i]) for i, k in enumerate(HQDN3D_KEYS)}
	else:
		_reject_unknown(op, ("op", "method", "intensity", "strength", "patch", "research"), "denoise")
		base = NLMEANS_PRESETS[intensity]
		params = {
			"strength": _number(op, "strength", 1, 30, base["strength"]),
			"patch": _odd_int(op, "patch", 3, 15, base["patch"]),
			"research": _odd_int(op, "research", 3, 35, base["research"]),
		}
		if params["research"] < params["patch"]:
			raise ValueError("'research' must be >= 'patch'")
	return {"method": method, "intensity": intensity, "params": params}


def build_denoise(op):
	cfg = normalize_denoise(op)
	p = cfg["params"]
	if cfg["method"] == "hqdn3d":
		vf = "hqdn3d=" + ":".join(_fmt(p[k]) for k in HQDN3D_KEYS)
	else:
		vf = "nlmeans=s=" + _fmt(p["strength"]) + ":p=" + str(p["patch"]) + ":r=" + str(p["research"])
	return ["-vf", vf] + ENCODE_ARGS


# ------------------------------------------------------------ color grade

EQ_DEFAULTS = {"brightness": 0.0, "contrast": 1.0, "saturation": 1.0, "gamma": 1.0}
EQ_RANGES = {"brightness": (-1.0, 1.0), "contrast": (0.0, 3.0),
			 "saturation": (0.0, 3.0), "gamma": (0.1, 10.0)}
TONE_SUFFIX = {"shadows": "s", "midtones": "m", "highlights": "h"}
CHANNELS = ("r", "g", "b")
CURVE_PRESETS = (
	"color_negative", "cross_process", "darker", "increase_contrast", "lighter",
	"linear_contrast", "medium_contrast", "negative", "strong_contrast", "vintage",
)
CURVE_CHANNELS = ("master", "red", "green", "blue")
COLOR_PRESETS = {
	"warm": {"saturation": 1.1,
			 "colorbalance": {"midtones": {"r": 0.08, "b": -0.08}, "highlights": {"r": 0.05, "b": -0.05}}},
	"cool": {"saturation": 1.05,
			 "colorbalance": {"midtones": {"r": -0.08, "b": 0.08}, "shadows": {"b": 0.05}}},
	"cinematic": {"contrast": 1.15, "saturation": 0.9,
				  "colorbalance": {"shadows": {"r": -0.04, "b": 0.08}, "highlights": {"r": 0.06, "b": -0.04}},
				  "curves": {"preset": "medium_contrast"}},
	"vivid": {"contrast": 1.1, "saturation": 1.4},
}


def _normalize_balance(value):
	if not isinstance(value, dict):
		raise ValueError("'colorbalance' must be an object with shadows/midtones/highlights")
	_reject_unknown(value, TONE_SUFFIX.keys(), "colorbalance")
	result = {}
	for tone, channels in value.items():
		if not isinstance(channels, dict):
			raise ValueError("colorbalance." + tone + " must be an object with r/g/b")
		_reject_unknown(channels, CHANNELS, "colorbalance." + tone)
		tone_values = {}
		for ch in CHANNELS:
			amount = _number(channels, ch, -1.0, 1.0, 0.0)
			if amount != 0.0:
				tone_values[ch] = amount
		if tone_values:
			result[tone] = tone_values
	return result


def _normalize_points(name, points):
	if not isinstance(points, (list, tuple)) or not 2 <= len(points) <= 16:
		raise ValueError("curves." + name + " must be a list of 2 to 16 [x, y] points")
	result, last_x = [], -1.0
	for pt in points:
		if not isinstance(pt, (list, tuple)) or len(pt) != 2:
			raise ValueError("curves." + name + " points must be [x, y] pairs")
		x = _number({"x": pt[0]}, "x", 0.0, 1.0, 0.0)
		y = _number({"y": pt[1]}, "y", 0.0, 1.0, 0.0)
		if x <= last_x:
			raise ValueError("curves." + name + " x values must be strictly increasing")
		last_x = x
		result.append((x, y))
	return result


def _normalize_curves(value):
	if not isinstance(value, dict):
		raise ValueError("'curves' must be an object")
	_reject_unknown(value, ("preset",) + CURVE_CHANNELS, "curves")
	result = {}
	if value.get("preset") is not None:
		if value["preset"] not in CURVE_PRESETS:
			raise ValueError("curves.preset must be one of: " + ", ".join(CURVE_PRESETS))
		result["preset"] = value["preset"]
	for channel in CURVE_CHANNELS:
		if value.get(channel) is not None:
			result[channel] = _normalize_points(channel, value[channel])
	return result


def normalize_color_grade(op):
	_reject_unknown(op, ("op", "preset", "colorbalance", "curves") + tuple(EQ_DEFAULTS), "color_grade")
	preset_name = op.get("preset")
	base = {}
	if preset_name is not None:
		if preset_name not in COLOR_PRESETS:
			raise ValueError("preset must be one of: " + ", ".join(COLOR_PRESETS))
		base = COLOR_PRESETS[preset_name]
	eq = {k: _number(op, k, lo, hi, base.get(k, EQ_DEFAULTS[k])) for k, (lo, hi) in EQ_RANGES.items()}
	eq_active = any(eq[k] != EQ_DEFAULTS[k] for k in eq)
	balance = _normalize_balance(op["colorbalance"] if "colorbalance" in op else base.get("colorbalance", {}))
	curves = _normalize_curves(op["curves"] if "curves" in op else base.get("curves", {}))
	if not (eq_active or balance or curves):
		raise ValueError("no adjustment requested: set brightness, contrast, saturation, gamma, "
						 "colorbalance, curves or a preset")
	return {"preset": preset_name, "eq": eq if eq_active else None,
			"colorbalance": balance, "curves": curves}


def build_color_grade(op):
	cfg = normalize_color_grade(op)
	filters = []
	if cfg["eq"]:
		filters.append("eq=" + ":".join(k + "=" + _fmt(v) for k, v in cfg["eq"].items()))
	if cfg["colorbalance"]:
		parts = []
		for tone, channels in cfg["colorbalance"].items():
			for ch, amount in channels.items():
				parts.append(ch + TONE_SUFFIX[tone] + "=" + _fmt(amount))
		filters.append("colorbalance=" + ":".join(parts))
	if cfg["curves"]:
		parts = []
		if "preset" in cfg["curves"]:
			parts.append("preset=" + cfg["curves"]["preset"])
		for channel in CURVE_CHANNELS:
			if channel in cfg["curves"]:
				pts = " ".join(_fmt(x) + "/" + _fmt(y) for x, y in cfg["curves"][channel])
				parts.append(channel + "='" + pts + "'")
		filters.append("curves=" + ":".join(parts))
	return ["-vf", ",".join(filters)] + ENCODE_ARGS