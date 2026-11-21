"""Lip sync for the scene-clip podcast (LatentSync on a Kaggle GPU, then pasted back).

Run inside podcast/ with lipsync/run/ holding timing.js and line*.wav (made by the workflow's audio mode).

  python ../scripts/lipsync_scenes.py prep    # retimed scenes + one speaker crop per line -> ../lipsync/run/jobs/
  (push, run the Kaggle notebook, download its outputs into ../lipsync/run/synced/)
  python ../scripts/lipsync_scenes.py paste   # paste the synced faces back -> scenes_synced/sceneN.mp4

The retimed scenes already match the voice timing, so compose_scenes.py uses them at speed 1.
"""
import json
import os
import subprocess
import sys

RUN = "../lipsync/run"
FPS = 25
SCALE = 2  # the speaker crop is upscaled so the face is big enough for the model
SIDE = {"dob": (0.0, 0.56), "doli": (0.44, 1.0)}  # Dob sits on the left, Doli on the right

T = json.loads(open(f"{RUN}/timing.js").read().split("=", 1)[1].strip().rstrip(";"))
lines = T["lines"]


def sh(*a):
    subprocess.run(a, check=True)


def probe(path, entry):
    return subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entry, "-of", "csv=p=0", path]).decode().strip()


def picture_rows(path):
    import numpy as np
    w, h = map(int, probe(path, "stream=width,height").split(","))
    frame = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", "1", "-i", path, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"])
    a = np.frombuffer(frame, np.uint8)[: w * h].reshape(h, w).astype(float)
    busy = np.where(a.std(axis=1) > 6)[0]
    top, bottom = int(busy.min()) + 2, int(busy.max()) - 2
    return w, top, (bottom - top) // 2 * 2


def spans():
    out = []
    for l in lines:
        if not out or out[-1][0] != l["scene"]:
            out.append([l["scene"], l["start"]])
    out[0][1] = 0
    return [(n, s, out[i + 1][1] if i + 1 < len(out) else T["total"]) for i, (n, s) in enumerate(out)]


def prep():
    os.makedirs(f"{RUN}/jobs", exist_ok=True)
    os.makedirs(f"{RUN}/retimed", exist_ok=True)
    jobs = []
    for n, s, e in spans():
        src = f"scenes/scene{n}.mp4"
        w, y0, h = picture_rows(src)
        clip = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", src]).decode())
        dur = e - s
        k = min(1.35, max(0.6, dur / clip))
        rt = f"{RUN}/retimed/scene{n}.mp4"
        sh("ffmpeg", "-v", "error", "-y", "-i", src, "-an", "-vf",
           f"crop={w // 2 * 2}:{h}:0:{y0},setpts={k:.4f}*(PTS-STARTPTS),fps={FPS},tpad=stop_mode=clone:stop_duration={dur + 1:.2f}",
           "-t", f"{dur:.3f}", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", rt)
        for i, l in enumerate(lines):
            if l["scene"] != n:
                continue
            a, b = l["start"] - s, l["end"] - s
            x0f, x1f = SIDE[l["speaker"]]
            cw = int(w * (x1f - x0f)) // 2 * 2
            cx = int(w * x0f)
            name = f"line{i}"
            sh("ffmpeg", "-v", "error", "-y", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", rt, "-vf",
               f"crop={cw}:{h}:{cx}:0,scale={cw * SCALE}:{h * SCALE}:flags=lanczos", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p",
               f"{RUN}/jobs/{name}.mp4")
            sh("ffmpeg", "-v", "error", "-y", "-i", f"{RUN}/line{i}.wav", "-ac", "1", "-ar", "16000", f"{RUN}/jobs/{name}.wav")
            jobs.append({"name": name, "scene": n, "at": round(a, 3), "x": cx, "w": cw, "h": h, "speaker": l["speaker"]})
    json.dump(jobs, open(f"{RUN}/jobs/jobs.json", "w"), indent=1)
    print(f"{len(jobs)} lip-sync jobs ready in {RUN}/jobs")


def paste():
    jobs = json.load(open(f"{RUN}/jobs/jobs.json"))
    os.makedirs("scenes_synced", exist_ok=True)
    for n, s, e in spans():
        mine = [j for j in jobs if j["scene"] == n and os.path.exists(f"{RUN}/synced/{j['name']}.mp4")]
        args, filt, last = ["ffmpeg", "-v", "error", "-y", "-i", f"{RUN}/retimed/scene{n}.mp4"], [], "[0:v]"
        for k, j in enumerate(mine, 1):
            args += ["-i", f"{RUN}/synced/{j['name']}.mp4"]
            filt.append(f"[{k}:v]scale={j['w']}:{j['h']}:flags=lanczos,setpts=PTS-STARTPTS+{j['at']}/TB[f{k}]")
            filt.append(f"{last}[f{k}]overlay={j['x']}:0:eof_action=pass[o{k}]")
            last = f"[o{k}]"
        out = f"scenes_synced/scene{n}.mp4"
        if mine:
            args += ["-filter_complex", ";".join(filt), "-map", last]
        args += ["-an", "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", out]
        sh(*args)
        print(f"scene{n}: {len(mine)} synced lines")


{"prep": prep, "paste": paste}[sys.argv[1]]()
