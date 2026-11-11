import sys
import time
import requests

BASE = "http://127.0.0.1:8000"
video = sys.argv[1]


def run(file_id, ops, out_name=None):
    r = requests.post(BASE + "/jobs", json={"file_id": file_id, "operations": ops})
    if r.status_code != 200:
        return r.status_code, r.json().get("detail")
    job_id = r.json()["id"]
    while True:
        job = requests.get(BASE + "/jobs/" + job_id).json()
        if job["status"] in ("COMPLETED", "FAILED"):
            break
        time.sleep(0.5)
    if job["status"] == "FAILED":
        return "FAILED", job["error"]
    if out_name:
        data = requests.get(BASE + "/results/" + job_id).content
        with open(out_name, "wb") as f:
            f.write(data)
    return "COMPLETED", out_name


with open(video, "rb") as f:
    up = requests.post(BASE + "/files", files={"file": (video, f)})
print("upload:", up.status_code, up.json())
fid = up.json()["id"]

print("--- should be COMPLETED ---")
print("trim (existing feature):", run(fid, [{"op": "trim", "start": 0, "end": 1.5}], "out_trim.mp4"))
print("denoise hqdn3d:", run(fid, [{"op": "denoise", "method": "hqdn3d", "intensity": "medium"}], "out_hqdn3d.mp4"))
print("denoise nlmeans:", run(fid, [{"op": "denoise", "method": "nlmeans", "intensity": "medium"}], "out_nlmeans.mp4"))
print("color_grade:", run(fid, [{"op": "color_grade", "brightness": 0.1, "contrast": 1.2,
                                  "saturation": 1.3, "gamma": 1.1,
                                  "colorbalance": {"highlights": {"r": 0.1}}}], "out_color.mp4"))
print("chain:", run(fid, [{"op": "trim", "start": 0, "end": 2},
                          {"op": "denoise", "method": "hqdn3d"},
                          {"op": "color_grade", "preset": "cinematic"}], "out_chain.mp4"))

print("--- should be 400 (invalid parameters) ---")
print(run(fid, [{"op": "denoise", "method": "nlmeans", "strength": 999}]))
print(run(fid, [{"op": "denoise", "method": "nlmeans", "patch": 6}]))
print(run(fid, [{"op": "color_grade", "brightness": 5}]))
print(run(fid, [{"op": "color_grade"}]))
print(run(fid, [{"op": "color_grade", "preset": "sepia"}]))