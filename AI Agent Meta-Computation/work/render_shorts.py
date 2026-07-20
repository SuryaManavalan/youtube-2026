#!/usr/bin/env python3
"""Render vertical 1080x1920 shorts from FINAL1.mp4 per clips.json.

Talking-head spans: center crop 608x1080 -> 1080x1920.
Scene spans: full frame letterboxed over blurred fill.
Shot boundaries come from work/shotmap.json, refined to 0.25s here.
Word-timed karaoke captions (ASS) from work/transcript_raw.json.

Usage: python3 render_shorts.py [slug ...]   (no args = all clips)
"""
import json, os, subprocess, sys
import numpy as np

EP = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORK = os.path.join(EP, "work")
OUT = os.path.join(EP, "SHORTS")
VID = json.load(open(os.path.join(WORK, "episode.json")))["video"]
W, H = 64, 36

def grab_small(t):
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(t), "-i", VID, "-frames:v", "1",
         "-vf", f"scale={W}:{H}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True).stdout
    if len(out) != W * H * 3:
        return None
    return np.frombuffer(out, np.uint8).reshape(H, W, 3).astype(np.float32)

REFS = [grab_small(t) for t in (120, 240, 480)]

def classify(t):
    f = grab_small(t)
    if f is None:
        return "scene"
    d = min(float(np.mean(np.abs(f - r))) for r in REFS)
    return "head" if d < 25.0 else "scene"

# ---- shotmap with refined boundaries (cached) ----
FINE = os.path.join(WORK, "shotmap_fine.json")
if os.path.exists(FINE):
    SEGS = json.load(open(FINE))
else:
    SEGS = json.load(open(os.path.join(WORK, "shotmap.json")))
    for i in range(len(SEGS) - 1):
        b = SEGS[i]["end"]          # coarse boundary, 2s grid
        lo, hi = b - 2.0, b
        left_t = SEGS[i]["type"]
        while hi - lo > 0.25:
            mid = (lo + hi) / 2
            if classify(mid) == left_t:
                lo = mid
            else:
                hi = mid
        SEGS[i]["end"] = SEGS[i + 1]["start"] = round(hi, 2)
    json.dump(SEGS, open(FINE, "w"), indent=1)
    print("refined shot boundaries cached")

def shot_type(t):
    for s in SEGS:
        if s["start"] <= t < s["end"]:
            return s["type"]
    return "scene"

def spans_for(a, b):
    """Split [a,b) into (start, end, type) spans along shot boundaries."""
    cuts = [a] + [s["end"] for s in SEGS if a < s["end"] < b] + [b]
    out = []
    for x, y in zip(cuts, cuts[1:]):
        typ = shot_type((x + y) / 2)
        if out and out[-1][2] == typ:
            out[-1] = (out[-1][0], y, typ)
        else:
            out.append((x, y, typ))
    return out

# ---- words ----
RAW = json.load(open(os.path.join(WORK, "transcript_raw.json")))
WORDS = [w for w in RAW["words"] if w.get("type") == "word"]

def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}"

ASS_HEAD = """[Script Info]
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,DejaVu Sans,62,&H0000E7FF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,60,60,430,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

def build_ass(segments, path):
    """Karaoke captions on the output timeline: white text, yellow fill."""
    timeline = []   # (out_start, out_end, text) per word
    base = 0.0
    for a, b in segments:
        for w in WORDS:
            if a - 0.05 <= w["start"] < b:
                timeline.append((base + max(0, w["start"] - a),
                                 base + min(b, w["end"]) - a, w["text"].strip()))
        base += b - a
    lines, cur = [], []
    for i, wd in enumerate(timeline):
        cur.append(wd)
        gap = timeline[i + 1][0] - wd[1] if i + 1 < len(timeline) else 99
        if len(cur) >= 3 or gap > 0.7 or wd[2].endswith((".", "?", "!", ",")):
            lines.append(cur); cur = []
    if cur:
        lines.append(cur)
    with open(path, "w") as f:
        f.write(ASS_HEAD)
        for ln in lines:
            t0, t1 = ln[0][0], ln[-1][1]
            parts, prev = [], t0
            for ws, we, txt in ln:
                k = max(1, int(round((we - prev) * 100)))
                parts.append(f"{{\\k{k}}}{txt}")
                prev = we
            f.write(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},Cap,,0,0,0,,"
                    f"{' '.join(parts)}\n")

def render(clip):
    slug = clip["slug"]
    segs = [tuple(s) for s in clip["segments"]]
    ass = os.path.join(WORK, f"{slug}.ass")
    build_ass(segs, ass)
    fc, vlabels, alabels = [], [], []
    n = 0
    for a, b in segs:
        for x, y, typ in spans_for(a, b):
            v = f"v{n}"
            if typ == "head":
                fc.append(f"[0:v]trim={x:.3f}:{y:.3f},setpts=PTS-STARTPTS,"
                          f"crop=608:1080:656:0,scale=1080:1920,setsar=1[{v}]")
            else:
                fc.append(
                    f"[0:v]trim={x:.3f}:{y:.3f},setpts=PTS-STARTPTS,split[s{n}a][s{n}b];"
                    f"[s{n}a]scale=3414:1920,crop=1080:1920,boxblur=luma_radius=40:luma_power=2,"
                    f"eq=brightness=-0.15[bg{n}];"
                    f"[s{n}b]scale=1080:-2[fg{n}];"
                    f"[bg{n}][fg{n}]overlay=0:(H-h)/2,setsar=1[{v}]")
            vlabels.append(f"[{v}]")
            n += 1
        m = len(alabels)
        fc.append(f"[0:a]atrim={a:.3f}:{b:.3f},asetpts=PTS-STARTPTS[a{m}]")
        alabels.append(f"[a{m}]")
    fc.append("".join(vlabels) + f"concat=n={len(vlabels)}:v=1:a=0[vc]")
    fc.append("".join(alabels) + f"concat=n={len(alabels)}:v=0:a=1[ac]")
    fc.append(f"[vc]subtitles={ass.replace(':', '\\:')}[vs]")
    fc.append("[ac]loudnorm=I=-14:TP=-1.5:LRA=11[an]")
    out = os.path.join(OUT, f"{slug}.mp4")
    os.makedirs(OUT, exist_ok=True)
    cmd = ["ffmpeg", "-v", "error", "-i", VID,
           "-filter_complex", ";".join(fc),
           "-map", "[vs]", "-map", "[an]",
           "-c:v", "libx264", "-crf", "19", "-preset", "medium",
           "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
           out, "-y"]
    subprocess.run(cmd, check=True)
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", out], capture_output=True, text=True).stdout)
    print(f"{slug}: {dur:.1f}s -> {out}")

clips = json.load(open(os.path.join(EP, "clips.json")))["clips"]
want = set(sys.argv[1:])
for c in clips:
    if not want or c["slug"] in want:
        render(c)
