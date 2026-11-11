import requests

BASE = "http://127.0.0.1:8000"
with open("tone.wav", "rb") as f:
    fid = requests.post(BASE + "/files", files={"file": ("tone.wav", f)}).json()["id"]

for op in ({"op": "denoise", "method": "hqdn3d"}, {"op": "color_grade", "brightness": 0.1}):
    r = requests.post(BASE + "/jobs", json={"file_id": fid, "operations": [op]})
    print(r.status_code, r.json().get("detail"))