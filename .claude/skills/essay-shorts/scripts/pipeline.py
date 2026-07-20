#!/usr/bin/env python3
"""Video essay -> vertical shorts (essay-shorts skill).

Commands (episode dir = folder holding the FINAL export + work/):
  sentences <ep>              sentence-timestamped transcript from Scribe words
  shotmap   <ep> <t1,t2,t3>   head/scene map; t_i = visually-confirmed
                              talking-head reference timestamps (seconds)
  render    <ep> [slug ...]   render clips.json -> SHORTS/ (no slugs = all)

Prereqs: podcast-shorts pipeline init+transcribe already ran (episode.json
must point at the FINAL export — verify, init picks the largest file).
Requires: ffmpeg/ffprobe, numpy, DejaVu Sans.
"""
import json, os, subprocess, sys
import numpy as np

SMALL_W, SMALL_H = 64, 36
HEAD_THR = 25.0          # frame-diff below this vs refs => talking head
CROP_W = 608             # 9:16 slice of a 1920x1080 frame

def die(msg):
    sys.exit(f"ERROR: {msg}")

def paths(ep):
    ep = os.path.abspath(ep)
    return {"ep": ep, "work": os.path.join(ep, "work"),
            "out": os.path.join(ep, "SHORTS")}

def meta(P):
    f = os.path.join(P["work"], "episode.json")
    if not os.path.exists(f):
        die("no work/episode.json — run podcast-shorts init first")
    return json.load(open(f))

def words(P):
    raw = json.load(open(os.path.join(P["work"], "transcript_raw.json")))
    return [w for w in raw["words"] if w.get("type") == "word"]

# ----------------------------------------------------------- sentences

def cmd_sentences(ep):
    P = paths(ep)
    ws = words(P)
    out, sent, t0 = [], [], None
    for w in ws:
        if t0 is None:
            t0 = w["start"]
        sent.append(w["text"])
        if w["text"].rstrip().endswith((".", "?", "!")):
            out.append((t0, w["end"], " ".join(sent)))
            sent, t0 = [], None
    if sent:
        out.append((t0, ws[-1]["end"], " ".join(sent)))
    dst = os.path.join(P["work"], "sentences.txt")
    with open(dst, "w") as f:
        for a, b, s in out:
            f.write(f"[{a:7.2f} {b:7.2f}] {s}\n")
    print(f"{len(out)} sentences -> {dst}")

# ------------------------------------------------------------- shotmap

def grab_small(video, t):
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(t), "-i", video, "-frames:v", "1",
         "-vf", f"scale={SMALL_W}:{SMALL_H}", "-f", "rawvideo",
         "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    if len(out) != SMALL_W * SMALL_H * 3:
        return None
    return np.frombuffer(out, np.uint8).reshape(SMALL_H, SMALL_W, 3).astype(np.float32)

def make_classifier(video, ref_ts):
    refs = [grab_small(video, t) for t in ref_ts]
    refs = [r for r in refs if r is not None]
    if not refs:
        die("could not grab reference frames")
    def classify(t):
        f = grab_small(video, t)
        if f is None:
            return "scene", 999.0
        d = min(float(np.mean(np.abs(f - r))) for r in refs)
        return ("head" if d < HEAD_THR else "scene"), d
    return classify

def cmd_shotmap(ep, ref_arg):
    P = paths(ep)
    M = meta(P)
    ref_ts = [float(x) for x in ref_arg.split(",")]
    classify = make_classifier(M["video"], ref_ts)
    rows, t = [], 0.0
    while t < M["duration"]:
        typ, d = classify(t)
        rows.append((t, typ, d))
        t += 2.0
    ds = np.array([d for _, _, d in rows])
    segs = []
    for t, typ, _ in rows:
        if segs and segs[-1]["type"] == typ:
            segs[-1]["end"] = t + 2.0
        else:
            segs.append({"start": t, "end": t + 2.0, "type": typ})
    # refine each boundary to 0.25s
    for i in range(len(segs) - 1):
        lo, hi = segs[i]["end"] - 2.0, segs[i]["end"]
        left = segs[i]["type"]
        while hi - lo > 0.25:
            mid = (lo + hi) / 2
            if classify(mid)[0] == left:
                lo = mid
            else:
                hi = mid
        segs[i]["end"] = segs[i + 1]["start"] = round(hi, 2)
    M["head_refs"] = ref_ts
    json.dump(M, open(os.path.join(P["work"], "episode.json"), "w"), indent=1)
    dst = os.path.join(P["work"], "shotmap_fine.json")
    json.dump(segs, open(dst, "w"), indent=1)
    print(f"diff stats: min={ds.min():.1f} max={ds.max():.1f} "
          f"median={np.median(ds):.1f} (threshold {HEAD_THR})")
    for s in segs:
        print(f"{s['start']:7.2f}-{s['end']:7.2f}  {s['type']}")
    print(f"-> {dst}  (sanity-check alternation, then write clips.json)")

# -------------------------------------------------------------- render

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

def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}"

def build_ass(ws, segments, path):
    """Karaoke captions on the output timeline (white text, yellow fill)."""
    timeline, base = [], 0.0
    for a, b in segments:
        for w in ws:
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
            for wst, wen, txt in ln:
                k = max(1, int(round((wen - prev) * 100)))
                parts.append(f"{{\\k{k}}}{txt}")
                prev = wen
            f.write(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},Cap,,0,0,0,,"
                    f"{' '.join(parts)}\n")

def spans_for(segs, a, b):
    """Split [a,b) into (start, end, type) spans along shot boundaries."""
    def shot_type(t):
        for s in segs:
            if s["start"] <= t < s["end"]:
                return s["type"]
        return "scene"
    cuts = [a] + [s["end"] for s in segs if a < s["end"] < b] + [b]
    out = []
    for x, y in zip(cuts, cuts[1:]):
        typ = shot_type((x + y) / 2)
        if out and out[-1][2] == typ:
            out[-1] = (out[-1][0], y, typ)
        else:
            out.append((x, y, typ))
    return out

def render_clip(P, M, segs, ws, clip):
    slug = clip["slug"]
    segments = [tuple(s) for s in clip["segments"]]
    ass = os.path.join(P["work"], f"{slug}.ass")
    build_ass(ws, segments, ass)
    crop_x = (M["width"] - CROP_W) // 2
    fc, vlabels, alabels, n = [], [], [], 0
    for a, b in segments:
        for x, y, typ in spans_for(segs, a, b):
            v = f"v{n}"
            if typ == "head":
                fc.append(f"[0:v]trim={x:.3f}:{y:.3f},setpts=PTS-STARTPTS,"
                          f"crop={CROP_W}:1080:{crop_x}:0,"
                          f"scale=1080:1920,setsar=1[{v}]")
            else:
                fc.append(
                    f"[0:v]trim={x:.3f}:{y:.3f},setpts=PTS-STARTPTS,split[s{n}a][s{n}b];"
                    f"[s{n}a]scale=3414:1920,crop=1080:1920,"
                    f"boxblur=luma_radius=40:luma_power=2,eq=brightness=-0.15[bg{n}];"
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
    os.makedirs(P["out"], exist_ok=True)
    out = os.path.join(P["out"], f"{slug}.mp4")
    subprocess.run(
        ["ffmpeg", "-v", "error", "-i", M["video"],
         "-filter_complex", ";".join(fc), "-map", "[vs]", "-map", "[an]",
         "-c:v", "libx264", "-crf", "19", "-preset", "medium",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
         out, "-y"], check=True)
    dur = float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", out], capture_output=True, text=True).stdout)
    warn = "  ** OVER 60s **" if dur >= 60 else ""
    print(f"{slug}: {dur:.1f}s -> {out}{warn}")

def cmd_render(ep, slugs):
    P = paths(ep)
    M = meta(P)
    sm = os.path.join(P["work"], "shotmap_fine.json")
    if not os.path.exists(sm):
        die("no work/shotmap_fine.json — run shotmap first")
    segs = json.load(open(sm))
    ws = words(P)
    clips = json.load(open(os.path.join(P["ep"], "clips.json")))["clips"]
    want = set(slugs)
    for c in clips:
        if not want or c["slug"] in want:
            render_clip(P, M, segs, ws, c)

# ---------------------------------------------------------------- main

def main():
    if len(sys.argv) < 3:
        die(__doc__)
    cmd, ep = sys.argv[1], sys.argv[2]
    if cmd == "sentences":
        cmd_sentences(ep)
    elif cmd == "shotmap":
        if len(sys.argv) < 4:
            die("shotmap needs head reference timestamps, e.g. 120,240,480")
        cmd_shotmap(ep, sys.argv[3])
    elif cmd == "render":
        cmd_render(ep, sys.argv[3:])
    else:
        die(f"unknown command {cmd}\n{__doc__}")

main()
