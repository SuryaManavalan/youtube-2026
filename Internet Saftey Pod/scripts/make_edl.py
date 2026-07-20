#!/usr/bin/env python3
"""Build a word-accurate EDL from clip definitions.

Each segment is (approx_start, approx_end, speaker, shot). The script snaps
start to the first word starting >= approx_start - 0.4 belonging to that
speaker, and end to the last word ending <= approx_end + 0.4, then adds
lead-in/out padding. Outputs work/edl.json and prints a summary with the
actual text captured per segment so cuts can be sanity-checked.

shot: "solo"    -> full-frame crop of the segment speaker's tile
      "stacked" -> both tiles stacked
"""
import json
import os

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRANSCRIPT = os.path.join(BASE, "work", "transcript_raw.json")
OUT = os.path.join(BASE, "work", "edl.json")

PAD_IN = 0.15   # seconds of lead-in before first word
PAD_OUT = 0.25  # seconds after last word

def hms(t):
    h, r = divmod(t, 3600)
    m, s = divmod(r, 60)
    return int(h) * 3600 + int(m) * 60 + s if False else t

def T(s):
    """'H:MM:SS' or 'H:MM:SS.s' -> seconds"""
    parts = [float(p) for p in s.split(":")]
    return parts[0] * 3600 + parts[1] * 60 + parts[2]

# clip definitions: (title, slug, [segments])
# segment = (start, end, speaker, shot); speaker "any" = keep both (banter)
CLIPS = [
    ("It sounds like a confession", "01_confession", [
        ("0:20:33", "0:20:43", "speaker_0", "solo"),
        ("0:20:44", "0:20:57", "speaker_0", "solo"),
        ("0:21:09", "0:21:23", "speaker_0", "solo"),
        ("0:21:25", "0:21:28.5", "speaker_1", "stacked"),
        ("0:21:42", "0:22:01", "speaker_0", "solo"),
    ]),
    ("Homeschooled on the global stage", "02_homeschooled", [
        ("0:22:38.5", "0:23:05", "speaker_0", "solo"),
        ("0:23:05", "0:23:10", "speaker_1", "stacked"),
        ("0:24:12", "0:24:31", "speaker_0", "solo"),
    ]),
    ("Humanity 0.01 beta", "03_beta", [
        ("0:32:02", "0:32:26", "speaker_0", "solo"),
        ("0:32:29", "0:32:37", "speaker_0", "stacked"),
        ("0:33:22", "0:33:45", "speaker_1", "solo"),
    ]),
    ("A casino for kids", "04_casino", [
        ("0:35:48", "0:36:03", "speaker_0", "solo"),
        ("0:40:00", "0:40:13", "speaker_0", "solo"),
        ("0:40:13", "0:40:16", "speaker_1", "stacked"),
        ("0:40:17", "0:40:37", "speaker_0", "solo"),
    ]),
    ("Slinging emotional fluids", "05_fluids", [
        ("0:49:25", "0:49:39", "speaker_0", "solo"),
        ("0:49:54", "0:50:14", "speaker_0", "solo"),
        ("0:51:03", "0:51:14", "speaker_0", "stacked"),
        ("0:51:16", "0:51:20", "speaker_1", "stacked"),
    ]),
    ("The bidet theory of AI privacy", "06_bidet", [
        ("1:01:27", "1:01:34", "speaker_1", "solo"),
        ("1:02:07", "1:02:23", "speaker_0", "solo"),
        ("1:02:24", "1:02:40", "speaker_0", "solo"),
        ("1:02:51", "1:02:54", "speaker_0", "stacked"),
        ("1:02:54", "1:03:04", "speaker_1", "stacked"),
    ]),
    ("Stalking 2.0", "07_stalking", [
        ("1:13:24", "1:13:34", "speaker_0", "solo"),
        ("1:14:10", "1:14:47", "speaker_0", "solo"),
        ("1:14:48", "1:15:00", "speaker_1", "solo"),
    ]),
    ("My AI is editing this right now", "08_meta", [
        ("1:20:17", "1:20:26", "speaker_0", "solo"),
        ("1:20:53", "1:21:01.5", "any", "stacked"),
        ("1:21:02.5", "1:21:14", "speaker_1", "solo"),
        ("1:21:14", "1:21:18.5", "any", "stacked"),
    ]),
]


def main():
    words = [w for w in json.load(open(TRANSCRIPT))["words"] if w["type"] == "word"]
    edl = []
    for title, slug, segs in CLIPS:
        clip = {"title": title, "slug": slug, "segments": []}
        total = 0.0
        print(f"\n=== {slug}: {title}")
        for (s, e, spk, shot) in segs:
            s, e = T(s), T(e)
            seg_words = [w for w in words
                         if (spk == "any" or w["speaker_id"] == spk)
                         and w["start"] >= s - 0.4 and w["end"] <= e + 0.4]
            if not seg_words:
                print(f"  !! NO WORDS in {s}-{e} for {spk}")
                continue
            w0, w1 = seg_words[0], seg_words[-1]
            cut_in = max(0, w0["start"] - PAD_IN)
            cut_out = w1["end"] + PAD_OUT
            dur = cut_out - cut_in
            total += dur
            text = " ".join(w["text"] for w in seg_words)
            clip["segments"].append({
                "in": round(cut_in, 3), "out": round(cut_out, 3),
                "speaker": spk, "shot": shot, "text": text,
            })
            print(f"  [{cut_in:8.2f} -{cut_out:8.2f}] {dur:5.1f}s {spk} {shot:8s} {text[:80]}")
        clip["duration"] = round(total, 2)
        print(f"  TOTAL: {total:.1f}s")
        edl.append(clip)
    json.dump(edl, open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
