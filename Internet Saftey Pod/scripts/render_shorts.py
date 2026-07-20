#!/usr/bin/env python3
"""Render vertical 1080x1920 shorts from work/edl.json.

Shot types:
  solo    - full-bleed 9:16 crop of the segment speaker's tile
  stacked - both tiles cropped to 9:8 and stacked (speaker glow order kept)

Audio: per-speaker gain correction (mic imbalance) + per-clip loudnorm to
-14 LUFS. Segments get 20ms audio fades to avoid clicks at cuts.

Usage: python3 render_shorts.py [slug ...]   (no args = all clips)
"""
import json
import os
import subprocess
import sys

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(BASE, "RAW", "2026-07-19 16-03-26.mp4")
EDL = os.path.join(BASE, "work", "edl.json")
OUTDIR = os.path.join(BASE, "SHORTS")
TMP = os.path.join(BASE, "work", "tmp_segs")

# inner tile regions (green border excluded), full-res coords
TILES = {
    "top":    (462, 119, 882, 492),
    "bottom": (462, 630, 882, 492),
}
# which diarized speaker sits in which tile
SPEAKER_TILE = {"speaker_0": "bottom", "speaker_1": "top"}
# per-speaker gain correction in dB (speaker_0 mic is quieter)
GAIN = {"speaker_0": 1.6, "speaker_1": 0.0}
# horizontal offset of face center within tile, as fraction of tile width
FACE_X = {"top": 0.50, "bottom": 0.47}

W, H = 1080, 1920
FPS = 30


def solo_filter(tile):
    x, y, w, h = TILES[tile]
    cw = int(h * 9 / 16)  # 276 for 492 tall
    cx = int(w * FACE_X[tile] - cw / 2)
    cx = max(0, min(w - cw, cx))
    return (f"crop={w}:{h}:{x}:{y},crop={cw}:{h}:{cx}:0,"
            f"scale={W}:{H}:flags=lanczos,unsharp=5:5:0.4,setsar=1,fps={FPS}")


def stacked_filter():
    parts = []
    for name, out in (("top", "t"), ("bottom", "b")):
        x, y, w, h = TILES[name]
        cw = int(h * 9 / 8)  # 553 for 1080x960 half
        cx = int(w * FACE_X[name] - cw / 2)
        cx = max(0, min(w - cw, cx))
        parts.append(
            f"[0:v]crop={w}:{h}:{x}:{y},crop={cw}:{h}:{cx}:0,"
            f"scale={W}:{H//2}:flags=lanczos,unsharp=5:5:0.4[{out}]"
        )
    return ";".join(parts) + f";[t][b]vstack,setsar=1,fps={FPS}[v]"


def render_segment(seg, path):
    t0, t1 = seg["in"], seg["out"]
    dur = t1 - t0
    gain = GAIN.get(seg["speaker"], 0.8)  # "any": split the difference
    af = (f"volume={gain}dB,afade=t=in:d=0.02,"
          f"afade=t=out:st={max(0, dur - 0.02)}:d=0.02,"
          f"aresample=48000,asetpts=PTS-STARTPTS")
    cmd = ["ffmpeg", "-v", "error", "-ss", str(t0), "-t", str(dur), "-i", SRC]
    if seg["shot"] == "stacked":
        cmd += ["-filter_complex", stacked_filter() + f";[0:a]{af}[a]",
                "-map", "[v]", "-map", "[a]"]
    else:
        tile = SPEAKER_TILE[seg["speaker"]]
        cmd += ["-vf", solo_filter(tile) + ",setpts=PTS-STARTPTS", "-af", af]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-c:a", "aac", "-b:a", "192k", "-video_track_timescale", "90000",
            path, "-y"]
    subprocess.run(cmd, check=True)


def render_clip(clip):
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(OUTDIR, exist_ok=True)
    seg_files = []
    for i, seg in enumerate(clip["segments"]):
        p = os.path.join(TMP, f"{clip['slug']}_{i}.mp4")
        render_segment(seg, p)
        seg_files.append(p)
    lst = os.path.join(TMP, f"{clip['slug']}_list.txt")
    with open(lst, "w") as f:
        for p in seg_files:
            f.write(f"file '{p}'\n")
    out = os.path.join(OUTDIR, f"{clip['slug']}.mp4")
    # concat, then loudnorm the whole clip to -14 LUFS
    subprocess.run(
        ["ffmpeg", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst,
         "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
         "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", out, "-y"],
        check=True)
    print(f"rendered {out} ({clip['duration']}s)")


def main():
    clips = json.load(open(EDL))
    want = set(sys.argv[1:])
    for clip in clips:
        if want and clip["slug"] not in want:
            continue
        render_clip(clip)


if __name__ == "__main__":
    main()
