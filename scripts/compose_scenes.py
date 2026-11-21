"""Builds the podcast Short from animated scene clips (made from Gemini images with Grok Imagine).

Run inside podcast/ after make_dialogue.mjs:  python ../scripts/compose_scenes.py
Reads timing.js (line timings, cards, scene number per line) and assets/voice.mp3, and writes out/video.mp4:
  - each scene clip (scenes/sceneN.mp4) plays while its lines are spoken; it is gently slowed or sped up
    (0.6x to 1.35x) to fit, and holds its last frame if the lines are still longer
  - the colour bands the image tools leave above and below the picture are cropped away
  - title, number cards, subtitles and the dolidob.com pill are drawn on top
"""
import json
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H, FPS = 1080, 1920, 30
SCENE_Y = 520  # top of the picture area
NIGHT = (11, 20, 48)
COLORS = {"sky": "#93c5fd", "violet": "#c4b5fd", "pink": "#f9a8d4", "gold": "#fcd34d", "mint": "#6ee7b7"}
SPEAKER = {"dob": ("Dob", "#93c5fd"), "doli": ("Doli", "#fcd34d")}

T = json.loads(open("timing.js").read().split("=", 1)[1].strip().rstrip(";"))
os.makedirs("tmp/overlays", exist_ok=True)
os.makedirs("out", exist_ok=True)


def font(name, size, weight):
    f = ImageFont.truetype(f"fonts/{name}.ttf", size)
    f.set_variation_by_name(weight)
    return f


def probe(path, entry):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", entry, "-of", "csv=p=0", path])
    return out.decode().strip().split("\n")[0]


def picture_rows(path):
    """Rows of the clip that hold the picture (not the flat colour bands)."""
    frame = subprocess.check_output(["ffmpeg", "-v", "error", "-ss", "1", "-i", path, "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "gray", "-"])
    w, h = map(int, probe(path, "stream=width,height").split(","))
    a = np.frombuffer(frame, np.uint8)[: w * h].reshape(h, w).astype(float)
    busy = np.where(a.std(axis=1) > 6)[0]
    top, bottom = int(busy.min()) + 2, int(busy.max()) - 2
    return w, h, top, bottom


def wrap(draw, text, f, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=f) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    lines.append(cur)
    return lines


def rounded(size, radius, fill, outline=None):
    im = Image.new("RGBA", size, (0, 0, 0, 0))
    ImageDraw.Draw(im).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius, fill=fill, outline=outline, width=2)
    return im


# Static layer: background, title, footer, brand pill (the picture goes over the background).
bg = Image.new("RGBA", (W, H), NIGHT + (255,))
d = ImageDraw.Draw(bg)
for y in range(H):  # soft vertical glow
    k = max(0, 1 - abs(y - 960) / 1100)
    d.line([(0, y), (W, y)], fill=(int(11 + 14 * k), int(20 + 28 * k), int(48 + 60 * k), 255))
kick = font("Plex", 30, "Bold")
d.text((W / 2, 70), "THE DOLIDOB PAYCHECK PODCAST", font=kick, fill="#93c5fd", anchor="mm")
title = (T.get("title") or "").replace(" (2026)", "")
tf = font("Bricolage", 66, "ExtraBold")
for i, line in enumerate(wrap(d, title, tf, 960)):
    d.text((W / 2, 150 + i * 72), line, font=tf, fill="white", anchor="mm")
bg.save("tmp/overlays/bg.png")

top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(top)
pill = rounded((400, 84), 42, "#fcd34d")
top.alpha_composite(pill, (340, 1700))
d.text((W / 2, 1742), "dolidob.com", font=font("Bricolage", 46, "ExtraBold"), fill=NIGHT, anchor="mm")
d.text((W / 2, 1830), "Estimates only, not tax advice. 2026 rules.", font=font("Plex", 26, "Medium"), fill="#8fa4d8", anchor="mm")
top.save("tmp/overlays/top.png")

# Subtitles: one per line, from its start until the next line starts.
overlays = []  # (png, x, y, start, end)
lines = T["lines"]
for i, l in enumerate(lines):
    until = lines[i + 1]["start"] if i + 1 < len(lines) else T["total"]
    size = 40 if len(l["text"]) > 95 else 46
    f = font("Plex", size, "SemiBold")
    probe_d = ImageDraw.Draw(Image.new("RGBA", (10, 10)))
    rows = wrap(probe_d, l["text"], f, 860)
    h = 80 + len(rows) * int(size * 1.25) + 30
    im = rounded((940, h), 28, (11, 20, 48, 225), outline=(255, 255, 255, 50))
    dd = ImageDraw.Draw(im)
    name, col = SPEAKER[l["speaker"]]
    dd.text((470, 44), name.upper(), font=font("Bricolage", 32, "ExtraBold"), fill=col, anchor="mm")
    for j, r in enumerate(rows):
        dd.text((470, 92 + j * int(size * 1.25) + size // 2), r, font=f, fill="white", anchor="mm")
    p = f"tmp/overlays/sub{i}.png"
    im.save(p)
    overlays.append((p, 70, 1660 - h, l["start"], until))

# Number cards: from their line until the next card.
carded = [l for l in lines if l.get("card")]
for i, l in enumerate(carded):
    until = carded[i + 1]["start"] if i + 1 < len(carded) else T["total"]
    c = l["card"]
    im = rounded((820, 200), 32, (22, 34, 79, 238), outline=(255, 255, 255, 40))
    dd = ImageDraw.Draw(im)
    dd.text((410, 48), c["label"], font=font("Plex", 34, "SemiBold"), fill="#c9d6f5", anchor="mm")
    vs = 92 if len(c["value"]) <= 9 else 66
    dd.text((410, 130), c["value"], font=font("Bricolage", vs, "ExtraBold"), fill=COLORS.get(c["color"], "white"), anchor="mm")
    p = f"tmp/overlays/card{i}.png"
    im.save(p)
    overlays.append((p, 130, 300, l["start"], until))

# Scenes: start with their first line (the first scene starts at 0), end where the next scene starts.
scenes = []
for l in lines:
    n = l.get("scene")
    if n and (not scenes or scenes[-1][0] != n):
        scenes.append([n, l["start"]])
scenes[0][1] = 0
spans = [(n, s, scenes[i + 1][1] if i + 1 < len(scenes) else T["total"]) for i, (n, s) in enumerate(scenes)]

args = ["ffmpeg", "-y", "-loop", "1", "-framerate", str(FPS), "-t", str(T["total"]), "-i", "tmp/overlays/bg.png"]
filters, last, idx = [], "[0:v]", 1
for n, s, e in spans:
    path = f"scenes/scene{n}.mp4"
    w, h, y0, y1 = picture_rows(path)
    clip = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path]).decode())
    dur = e - s
    k = min(1.35, max(0.6, dur / clip))
    args += ["-i", path]
    filters.append(
        f"[{idx}:v]crop={w}:{y1 - y0}:0:{y0},setpts={k:.4f}*(PTS-STARTPTS),fps={FPS},scale={W}:-2:flags=lanczos,"
        f"tpad=stop_mode=clone:stop_duration={dur + 1:.2f},trim=0:{dur:.3f},setpts=PTS-STARTPTS+{s:.3f}/TB[s{idx}]"
    )
    filters.append(f"{last}[s{idx}]overlay=0:{SCENE_Y}:eof_action=pass:enable='between(t,{s:.3f},{e:.3f})'[b{idx}]")
    last, idx = f"[b{idx}]", idx + 1
for p, x, y, s, e in overlays + [("tmp/overlays/top.png", 0, 0, 0, T["total"])]:
    args += ["-i", p]
    filters.append(f"{last}[{idx}:v]overlay={x}:{y}:enable='between(t,{s:.3f},{e:.3f})'[b{idx}]")
    last, idx = f"[b{idx}]", idx + 1
args += ["-i", "assets/voice.mp3", "-filter_complex", ";".join(filters), "-map", last, "-map", f"{idx}:a",
         "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
         "-t", str(T["total"]), "-movflags", "+faststart", "out/video.mp4"]
subprocess.run(args, check=True)
print(f"Composed {len(spans)} scenes, {T['total']} s -> out/video.mp4")
