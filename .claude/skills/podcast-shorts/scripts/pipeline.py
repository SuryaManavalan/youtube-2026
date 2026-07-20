#!/usr/bin/env python3
"""Discord-podcast → vertical YouTube Shorts pipeline.

One orchestrator, five idempotent steps. Run `status` at any time to see
what's done and what to do next.

    python3 pipeline.py status     <episode-dir>
    python3 pipeline.py init       <episode-dir>
    python3 pipeline.py transcribe <episode-dir>
    python3 pipeline.py analyze    <episode-dir>
    python3 pipeline.py edl        <episode-dir>
    python3 pipeline.py render     <episode-dir> [slug ...]

<episode-dir> is a folder containing (anywhere inside it, e.g. in RAW/) one
OBS screen recording of a 2-person Discord call. All derived artifacts live
in <episode-dir>/work/; finished clips land in <episode-dir>/SHORTS/.

The only hand-authored file is <episode-dir>/clips.json (the editorial cut
list — see assets/clips_template.json in the skill folder).

Requires: ffmpeg/ffprobe, numpy, curl. ElevenLabs key in $ELEVENLABS_API_KEY
or ~/.elevenlabs_key.
"""
import json
import os
import re
import subprocess
import sys

import numpy as np

VIDEO_EXT = (".mp4", ".mkv", ".mov")
OUT_W, OUT_H, OUT_FPS = 1080, 1920, 30
PAD_IN, PAD_OUT = 0.15, 0.25   # seconds around snapped word boundaries
LUFS_TARGET = -14


# ---------------------------------------------------------------- helpers

def die(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)


def paths(ep):
    ep = os.path.abspath(ep)
    w = os.path.join(ep, "work")
    return {
        "ep": ep,
        "work": w,
        "meta": os.path.join(w, "episode.json"),
        "audio": os.path.join(w, "audio_16k.mp3"),
        "raw_json": os.path.join(w, "transcript_raw.json"),
        "turns_txt": os.path.join(w, "transcript_turns.txt"),
        "turns_json": os.path.join(w, "transcript_turns.json"),
        "border_csv": os.path.join(w, "active_speaker.csv"),
        "clips": os.path.join(ep, "clips.json"),
        "edl": os.path.join(w, "edl.json"),
        "shorts": os.path.join(ep, "SHORTS"),
        "tmp": os.path.join(w, "tmp_segs"),
    }


def load_meta(P):
    if not os.path.exists(P["meta"]):
        die(f"{P['meta']} missing — run `init` first")
    return json.load(open(P["meta"]))


def save_meta(P, meta):
    json.dump(meta, open(P["meta"], "w"), indent=1)


def ffprobe_json(video):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json",
         "-show_format", "-show_streams", video],
        capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def parse_ts(s):
    """seconds, 'MM:SS', 'H:MM:SS', optionally with .fraction"""
    if isinstance(s, (int, float)):
        return float(s)
    parts = [float(p) for p in s.split(":")]
    while len(parts) < 3:
        parts.insert(0, 0.0)
    return parts[0] * 3600 + parts[1] * 60 + parts[2]


def fmt_ts(t):
    h, r = divmod(int(t), 3600)
    m, s = divmod(r, 60)
    return f"{h}:{m:02d}:{s:02d}"


def green_mask(img):
    """Discord active-speaker border green (works on RGB int arrays)."""
    r, g, b = img[..., 0], img[..., 1], img[..., 2]
    return (g > 110) & (g > r + 35) & (g > b + 35)


def grab_frame(video, t):
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", str(t), "-i", video,
         "-frames:v", "1", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True).stdout
    return out


# ------------------------------------------------------------------ init

def find_video(ep):
    cands = []
    for root, dirs, files in os.walk(ep):
        if any(x in root for x in ("work", "SHORTS", "tmp")):
            continue
        for f in files:
            if f.lower().endswith(VIDEO_EXT):
                p = os.path.join(root, f)
                cands.append((os.path.getsize(p), p))
    if not cands:
        die(f"no video file ({'/'.join(VIDEO_EXT)}) found under {ep}")
    return sorted(cands)[-1][1]  # largest


def cmd_init(ep):
    P = paths(ep)
    os.makedirs(P["work"], exist_ok=True)
    video = find_video(P["ep"])
    info = ffprobe_json(video)
    vs = next(s for s in info["streams"] if s["codec_type"] == "video")
    meta = {
        "video": video,
        "duration": float(info["format"]["duration"]),
        "width": vs["width"], "height": vs["height"],
    }
    save_meta(P, meta)
    print(f"video: {video}")
    print(f"{vs['width']}x{vs['height']}, {meta['duration']:.0f}s")
    if not os.path.exists(P["audio"]):
        print("extracting audio…")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-i", video, "-vn", "-ac", "1",
             "-ar", "16000", "-b:a", "32k", P["audio"], "-y"], check=True)
    print("init done → next: transcribe")


# ------------------------------------------------------------ transcribe

def get_api_key():
    k = os.environ.get("ELEVENLABS_API_KEY")
    if not k:
        f = os.path.expanduser("~/.elevenlabs_key")
        if os.path.exists(f):
            k = open(f).read().strip()
    if not k:
        die("no ElevenLabs key: set $ELEVENLABS_API_KEY or write it to "
            "~/.elevenlabs_key (ask the user for the key)")
    return k


def build_turns(P):
    words = [w for w in json.load(open(P["raw_json"]))["words"]
             if w["type"] == "word"]
    turns, cur = [], None
    for w in words:
        if cur and w["speaker_id"] == cur["spk"] and w["start"] - cur["end"] < 3.0:
            cur["text"].append(w["text"])
            cur["end"] = w["end"]
        else:
            if cur:
                turns.append(cur)
            cur = {"spk": w["speaker_id"], "start": w["start"],
                   "end": w["end"], "text": [w["text"]]}
    if cur:
        turns.append(cur)
    with open(P["turns_txt"], "w") as f:
        for t in turns:
            f.write(f"[{fmt_ts(t['start'])} - {fmt_ts(t['end'])}] "
                    f"{t['spk']}: {' '.join(t['text'])}\n\n")
    for t in turns:
        t["text"] = " ".join(t["text"])
    json.dump(turns, open(P["turns_json"], "w"))
    return turns


def cmd_transcribe(ep):
    P = paths(ep)
    if os.path.exists(P["raw_json"]):
        print("transcript exists, rebuilding turns only")
        build_turns(P)
        print(f"→ {P['turns_txt']}\nnext: analyze")
        return
    key = get_api_key()
    print("uploading to ElevenLabs Scribe (takes ~2-4 min for long calls)…")
    r = subprocess.run(
        ["curl", "-sS", "-X", "POST",
         "https://api.elevenlabs.io/v1/speech-to-text",
         "-H", f"xi-api-key: {key}",
         "-F", "model_id=scribe_v1", "-F", "diarize=true",
         "-F", "num_speakers=2", "-F", "timestamps_granularity=word",
         "-F", f"file=@{P['audio']}",
         "-o", P["raw_json"], "-w", "%{http_code}"],
        capture_output=True, text=True)
    if r.stdout.strip() != "200":
        err = open(P["raw_json"]).read()[:500] if os.path.exists(P["raw_json"]) else ""
        os.path.exists(P["raw_json"]) and os.remove(P["raw_json"])
        die(f"ElevenLabs HTTP {r.stdout.strip()}: {err}")
    turns = build_turns(P)
    print(f"{len(turns)} turns → {P['turns_txt']}\nnext: analyze")


# --------------------------------------------------------------- analyze

def detect_tiles(meta):
    """Find the two camera tiles by sampling frames and locating the green
    active-speaker border. Returns (tiles, layout)."""
    video, dur = meta["video"], meta["duration"]
    W, H = meta["width"], meta["height"]
    rects = []
    for i in range(72):
        t = dur * (i + 0.5) / 72
        buf = grab_frame(video, t)
        if len(buf) < W * H * 3:
            continue
        img = np.frombuffer(buf[:W * H * 3], dtype=np.uint8).reshape(H, W, 3).astype(int)
        m = green_mask(img)
        if m.sum() < 400:
            continue
        ys, xs = np.where(m)
        x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
        w, h = x1 - x0, y1 - y0
        if w < 150 or h < 100 or not (1.1 < w / h < 2.4):
            continue  # not a single 16:9-ish tile border
        rects.append((x0, y0, x1, y1))
    if len(rects) < 4:
        die("could not detect tile layout from green borders — is this a "
            "Discord call recording with an active-speaker border?")
    # cluster by center
    clusters = []
    for r in rects:
        cx, cy = (r[0] + r[2]) / 2, (r[1] + r[3]) / 2
        for c in clusters:
            if abs(cx - c["cx"]) < 60 and abs(cy - c["cy"]) < 60:
                c["rects"].append(r)
                break
        else:
            clusters.append({"cx": cx, "cy": cy, "rects": [r]})
        clusters.sort(key=lambda c: -len(c["rects"]))
    if len(clusters) < 2:
        die(f"only found {len(clusters)} tile(s) — need 2 speakers")
    tiles = []
    for c in clusters[:2]:
        arr = np.array(c["rects"])
        x0, y0 = int(np.median(arr[:, 0])), int(np.median(arr[:, 1]))
        x1, y1 = int(np.median(arr[:, 2])), int(np.median(arr[:, 3]))
        tiles.append([x0 + 4, y0 + 4, (x1 - x0) - 8, (y1 - y0) - 8])  # inner
    a, b = tiles
    stacked = abs((a[1] + a[3] / 2) - (b[1] + b[3] / 2)) > \
              abs((a[0] + a[2] / 2) - (b[0] + b[2] / 2))
    key = (lambda t: t[1]) if stacked else (lambda t: t[0])
    a, b = sorted([a, b], key=key)
    return {"A": a, "B": b}, ("stacked" if stacked else "side")


def scan_borders(meta, tiles, layout, out_csv):
    """1fps scan: which tile shows the green border each second."""
    video = meta["video"]
    (ax, ay, aw, ah), (bx, by, bw, bh) = tiles["A"], tiles["B"]
    if layout == "stacked":  # vertical strip through both left borders
        sx = min(ax, bx) - 8
        crop = f"crop=14:{meta['height']}:{sx}:0"
        length, spans = meta["height"], [(ay, ay + ah), (by, by + bh)]
        reshape = lambda img: img
    else:  # horizontal strip through both top borders
        sy = min(ay, by) - 8
        crop = f"crop={meta['width']}:14:0:{sy}"
        length, spans = meta["width"], [(ax, ax + aw), (bx, bx + bw)]
        reshape = lambda img: img.transpose(1, 0, 2)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-i", video, "-vf", f"fps=1,{crop}",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        stdout=subprocess.PIPE)
    if layout == "stacked":
        fh, fw = length, 14
    else:
        fh, fw = 14, length
    nbytes = fw * fh * 3
    rows, t = [], 0
    while True:
        buf = proc.stdout.read(nbytes)
        if len(buf) < nbytes:
            break
        img = np.frombuffer(buf, dtype=np.uint8).reshape(fh, fw, 3).astype(int)
        m = green_mask(reshape(img))  # rows = along-tile axis after reshape
        flags = [int(m[s0:s1].sum() > 40) for (s0, s1) in spans]
        rows.append(f"{t},{flags[0]},{flags[1]}")
        t += 1
    proc.wait()
    with open(out_csv, "w") as f:
        f.write("t,A,B\n" + "\n".join(rows) + "\n")


def cmd_analyze(ep):
    P = paths(ep)
    meta = load_meta(P)
    if not os.path.exists(P["turns_json"]):
        die("no transcript — run `transcribe` first")
    turns = json.load(open(P["turns_json"]))

    if "tiles" not in meta:
        print("detecting tile layout…")
        meta["tiles"], meta["layout"] = detect_tiles(meta)
        save_meta(P, meta)
    print(f"layout={meta['layout']} tiles={meta['tiles']}")

    if not os.path.exists(P["border_csv"]):
        print("scanning active-speaker border at 1fps (few minutes)…")
        scan_borders(meta, meta["tiles"], meta["layout"], P["border_csv"])

    # map diarized speakers → tiles
    tl = {}
    for line in open(P["border_csv"]).read().splitlines()[1:]:
        t, a, b = line.split(",")
        tl[int(t)] = (int(a), int(b))
    from collections import Counter
    score = {}
    for t in turns:
        if t["end"] - t["start"] < 1.5:
            continue
        c = score.setdefault(t["spk"], Counter())
        for sec in range(int(t["start"]) + 1, int(t["end"])):
            a, b = tl.get(sec, (0, 0))
            if a and not b:
                c["A"] += 1
            elif b and not a:
                c["B"] += 1
    speakers = sorted(score)
    if len(speakers) < 2:
        die("need 2 diarized speakers")
    s0, s1 = speakers[0], speakers[1]
    m0 = "A" if score[s0]["A"] >= score[s0]["B"] else "B"
    m1 = "B" if m0 == "A" else "A"
    conf0 = score[s0][m0] / max(1, sum(score[s0].values()))
    conf1 = score[s1][m1] / max(1, sum(score[s1].values()))
    if conf0 < 0.8 or conf1 < 0.8:
        print(f"WARNING low mapping confidence: {dict(score[s0])} {dict(score[s1])}")
    meta["speaker_tile"] = {s0: m0, s1: m1}
    print(f"speaker mapping: {meta['speaker_tile']} "
          f"(confidence {conf0:.0%}/{conf1:.0%})")

    # per-speaker loudness → gain correction
    lvl = {}
    for spk in (s0, s1):
        longest = sorted((t for t in turns if t["spk"] == spk),
                         key=lambda t: t["start"] - t["end"])[:10]
        vals = []
        for t in longest:
            out = subprocess.run(
                ["ffmpeg", "-v", "info", "-ss", str(t["start"]),
                 "-t", str(t["end"] - t["start"]), "-i", P["audio"],
                 "-af", "astats=metadata=1", "-f", "null", "-"],
                capture_output=True, text=True).stderr
            m = re.findall(r"RMS level dB: (-?[\d.]+)", out)
            if m:
                vals.append(float(m[-1]))
        lvl[spk] = sum(vals) / len(vals)
    loudest = max(lvl.values())
    meta["gain_db"] = {s: round(loudest - v, 2) for s, v in lvl.items()}
    print(f"levels: { {s: round(v,1) for s,v in lvl.items()} } "
          f"→ gains {meta['gain_db']}")
    save_meta(P, meta)
    print("analyze done → next: write clips.json, then `edl`")


# ------------------------------------------------------------------- edl

def cmd_edl(ep):
    P = paths(ep)
    meta = load_meta(P)
    if not os.path.exists(P["clips"]):
        die(f"{P['clips']} missing — write the editorial cut list first "
            "(see assets/clips_template.json in the skill)")
    spec = json.load(open(P["clips"]))
    words = [w for w in json.load(open(P["raw_json"]))["words"]
             if w["type"] == "word"]
    known = set(meta["speaker_tile"])
    edl, problems = [], []
    for clip in spec["clips"]:
        out = {"slug": clip["slug"], "title": clip.get("title", clip["slug"]),
               "segments": []}
        total = 0.0
        print(f"\n=== {clip['slug']}")
        for seg in clip["segments"]:
            s, e = parse_ts(seg["start"]), parse_ts(seg["end"])
            spk, shot = seg["speaker"], seg.get("shot", "solo")
            if spk not in known and spk != "any":
                problems.append(f"{clip['slug']}: unknown speaker {spk}")
                continue
            sw = [w for w in words
                  if (spk == "any" or w["speaker_id"] == spk)
                  and w["start"] >= s - 0.4 and w["end"] <= e + 0.4]
            if not sw:
                problems.append(f"{clip['slug']}: no words in "
                                f"{seg['start']}–{seg['end']} for {spk}")
                continue
            cut_in = max(0.0, sw[0]["start"] - PAD_IN)
            cut_out = sw[-1]["end"] + PAD_OUT
            total += cut_out - cut_in
            text = " ".join(w["text"] for w in sw)
            out["segments"].append({"in": round(cut_in, 3),
                                    "out": round(cut_out, 3),
                                    "speaker": spk, "shot": shot,
                                    "text": text})
            print(f"  [{cut_in:8.2f}-{cut_out:8.2f}] {cut_out-cut_in:5.1f}s "
                  f"{spk:9s} {shot:8s} {text[:70]}")
        out["duration"] = round(total, 2)
        print(f"  TOTAL {total:.1f}s" + ("  ⚠ OVER 60s!" if total > 60 else ""))
        if total > 60:
            problems.append(f"{clip['slug']}: {total:.1f}s exceeds 60s")
        edl.append(out)
    json.dump(edl, open(P["edl"], "w"), indent=1)
    print(f"\nwrote {P['edl']}")
    if problems:
        print("PROBLEMS to fix in clips.json, then rerun `edl`:")
        for p in problems:
            print(f"  - {p}")
    else:
        print("all clips OK → next: render")


# ---------------------------------------------------------------- render

ASS_HEAD = """[Script Info]
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,DejaVu Sans,62,&H0000E7FF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,2,60,60,430,1
Style: CapMid,DejaVu Sans,62,&H0000E7FF,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,5,2,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""


def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}"


def build_ass(words, segments, path):
    """Word-timed karaoke captions (white text, yellow fill) on the output
    timeline. segments: list of edl segments (in/out/speaker/shot). Solo
    shots caption in the lower third (style Cap); stacked shots at the seam
    between the two cams (style CapMid) so neither face is covered."""
    timeline, base = [], 0.0
    for seg in segments:
        a, b = seg["in"], seg["out"]
        spk, shot = seg["speaker"], seg.get("shot", "solo")
        style = "CapMid" if (shot == "stacked" or spk == "any") else "Cap"
        for w in words:
            if (spk == "any" or w["speaker_id"] == spk) \
                    and a - 0.05 <= w["start"] < b:
                timeline.append((base + max(0, w["start"] - a),
                                 base + min(b, w["end"]) - a,
                                 w["text"].strip(), style))
        base += b - a
    lines, cur = [], []
    for i, wd in enumerate(timeline):
        cur.append(wd)
        gap = timeline[i + 1][0] - wd[1] if i + 1 < len(timeline) else 99
        style_break = i + 1 < len(timeline) and timeline[i + 1][3] != wd[3]
        if len(cur) >= 3 or gap > 0.7 or style_break \
                or wd[2].endswith((".", "?", "!", ",")):
            lines.append(cur); cur = []
    if cur:
        lines.append(cur)
    with open(path, "w") as f:
        f.write(ASS_HEAD)
        for ln in lines:
            t0, t1 = ln[0][0], ln[-1][1]
            parts, prev = [], t0
            for wst, wen, txt, _ in ln:
                k = max(1, int(round((wen - prev) * 100)))
                parts.append(f"{{\\k{k}}}{txt}")
                prev = wen
            f.write(f"Dialogue: 0,{ass_time(t0)},{ass_time(t1)},{ln[0][3]},"
                    f",0,0,0,,{' '.join(parts)}\n")


def solo_vf(meta, tile):
    x, y, w, h = meta["tiles"][tile]
    fx = meta.get("face_x", {}).get(tile, 0.5)
    cw = int(h * 9 / 16)
    cx = max(0, min(w - cw, int(w * fx - cw / 2)))
    return (f"crop={w}:{h}:{x}:{y},crop={cw}:{h}:{cx}:0,"
            f"scale={OUT_W}:{OUT_H}:flags=lanczos,unsharp=5:5:0.4,"
            f"setsar=1,fps={OUT_FPS}")


def stacked_fc(meta):
    parts = []
    for tile, lbl in (("A", "t"), ("B", "b")):
        x, y, w, h = meta["tiles"][tile]
        fx = meta.get("face_x", {}).get(tile, 0.5)
        cw = int(h * 9 / 8)
        cx = max(0, min(w - cw, int(w * fx - cw / 2)))
        parts.append(f"[0:v]crop={w}:{h}:{x}:{y},crop={cw}:{h}:{cx}:0,"
                     f"scale={OUT_W}:{OUT_H//2}:flags=lanczos,"
                     f"unsharp=5:5:0.4[{lbl}]")
    return ";".join(parts) + f";[t][b]vstack,setsar=1,fps={OUT_FPS}[v]"


def cmd_render(ep, slugs):
    P = paths(ep)
    meta = load_meta(P)
    edl = json.load(open(P["edl"]))
    os.makedirs(P["tmp"], exist_ok=True)
    os.makedirs(P["shorts"], exist_ok=True)
    gains = meta.get("gain_db", {})
    all_words = [w for w in json.load(open(P["raw_json"]))["words"]
                 if w["type"] == "word"]
    for clip in edl:
        if slugs and clip["slug"] not in slugs:
            continue
        seg_files = []
        for i, seg in enumerate(clip["segments"]):
            p = os.path.join(P["tmp"], f"{clip['slug']}_{i}.mp4")
            t0, dur = seg["in"], seg["out"] - seg["in"]
            gain = gains.get(seg["speaker"],
                             sum(gains.values()) / max(1, len(gains)))
            af = (f"volume={gain}dB,afade=t=in:d=0.02,"
                  f"afade=t=out:st={max(0, dur-0.02)}:d=0.02,"
                  f"aresample=48000,asetpts=PTS-STARTPTS")
            cmd = ["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(dur),
                   "-i", meta["video"]]
            if seg["shot"] == "stacked" or seg["speaker"] == "any":
                cmd += ["-filter_complex", stacked_fc(meta) + f";[0:a]{af}[a]",
                        "-map", "[v]", "-map", "[a]"]
            else:
                tile = meta["speaker_tile"][seg["speaker"]]
                cmd += ["-vf", solo_vf(meta, tile) + ",setpts=PTS-STARTPTS",
                        "-af", af]
            cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19",
                    "-c:a", "aac", "-b:a", "192k",
                    "-video_track_timescale", "90000", p, "-y"]
            subprocess.run(cmd, check=True)
            seg_files.append(p)
        lst = os.path.join(P["tmp"], f"{clip['slug']}_list.txt")
        with open(lst, "w") as f:
            f.writelines(f"file '{p}'\n" for p in seg_files)
        ass = os.path.join(P["tmp"], f"{clip['slug']}.ass")
        build_ass(all_words, clip["segments"], ass)
        out = os.path.join(P["shorts"], f"{clip['slug']}.mp4")
        subprocess.run(
            ["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0",
             "-i", lst, "-af", f"loudnorm=I={LUFS_TARGET}:TP=-1.5:LRA=11",
             "-vf", f"subtitles={ass.replace(':', chr(92) + ':')}",
             "-c:v", "libx264", "-preset", "medium", "-crf", "19",
             "-c:a", "aac", "-b:a", "192k", out, "-y"],
            check=True)
        print(f"rendered {out} ({clip['duration']}s)")


# ---------------------------------------------------------------- status

def cmd_status(ep):
    P = paths(ep)
    steps = [
        ("init", os.path.exists(P["meta"]) and os.path.exists(P["audio"]),
         "python3 pipeline.py init <ep>  (finds video, extracts audio)"),
        ("transcribe", os.path.exists(P["turns_json"]),
         "python3 pipeline.py transcribe <ep>  (needs ElevenLabs key)"),
        ("analyze",
         os.path.exists(P["meta"]) and "gain_db" in
         (json.load(open(P["meta"])) if os.path.exists(P["meta"]) else {}),
         "python3 pipeline.py analyze <ep>  (layout, speaker map, loudness)"),
        ("clips.json", os.path.exists(P["clips"]),
         f"read {P['turns_txt']} and hand-write {P['clips']} "
         "(the editorial step — see SKILL.md)"),
        ("edl", os.path.exists(P["edl"]),
         "python3 pipeline.py edl <ep>  (snap cuts to word boundaries)"),
        ("render",
         os.path.isdir(P["shorts"]) and len(os.listdir(P["shorts"])) > 0,
         "python3 pipeline.py render <ep>"),
    ]
    print(f"episode: {P['ep']}")
    nxt = None
    for name, done, how in steps:
        print(f"  [{'x' if done else ' '}] {name}")
        if not done and nxt is None:
            nxt = how
    print(f"\nNEXT → {nxt}" if nxt else "\nAll steps complete.")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    cmd, ep = sys.argv[1], sys.argv[2]
    if not os.path.isdir(ep):
        die(f"episode dir not found: {ep}")
    if cmd == "status":
        cmd_status(ep)
    elif cmd == "init":
        cmd_init(ep)
    elif cmd == "transcribe":
        cmd_transcribe(ep)
    elif cmd == "analyze":
        cmd_analyze(ep)
    elif cmd == "edl":
        cmd_edl(ep)
    elif cmd == "render":
        cmd_render(ep, set(sys.argv[3:]))
    else:
        die(f"unknown command {cmd}")


if __name__ == "__main__":
    main()
