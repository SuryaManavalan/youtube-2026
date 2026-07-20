---
name: essay-shorts
description: >-
  Turn a finished horizontal video essay (talking head + wojak/pepe parallax
  scene art, the parallax-scene house style) into vertical 1080x1920
  hook-first Shorts/Reels/TikToks (~8-9 clips, <60s) with automatic
  head-crop vs blur-fill scene framing, diarized word-accurate cuts, and
  burned-in karaoke captions. Use when the user wants shorts cut from a
  single-narrator video essay (an exported FINAL render in an episode
  folder). For 2-person Discord podcast recordings use podcast-shorts
  instead. Triggers: "shorts from the video essay", "cut up the video",
  "vertical clips from FINAL", "essay shorts".
---

# Video Essay → Shorts Pipeline

Variant of `podcast-shorts` for single-narrator video essays whose visuals
alternate between a centered talking head and full-frame wojak/pepe scene
art. First built for "AI Agent Meta-Computation" (2026-07); that episode's
`work/render_shorts.py` is superseded by this skill.

Steps 1–2 (probe + ElevenLabs Scribe transcription) reuse the
podcast-shorts orchestrator; everything after is this skill's own script:

```
python3 .claude/skills/podcast-shorts/scripts/pipeline.py init "<ep>"
python3 .claude/skills/podcast-shorts/scripts/pipeline.py transcribe "<ep>"
python3 .claude/skills/essay-shorts/scripts/pipeline.py sentences "<ep>"
python3 .claude/skills/essay-shorts/scripts/pipeline.py shotmap "<ep>" <t1,t2,t3>
# (you) write <ep>/clips.json + CLIPS.md   ← the editorial step
python3 .claude/skills/essay-shorts/scripts/pipeline.py render "<ep>" [slug ...]
```

## Step notes

1. **init** picks the *largest* video file under the episode folder, which
   is often a raw camera render, not the final cut. Always verify the
   `video` path in `work/episode.json`; if wrong, rewrite it to point at
   the FINAL export (with its true duration/width/height from ffprobe),
   delete `work/audio_16k.mp3`, and re-extract audio yourself
   (`ffmpeg -i FINAL.mp4 -vn -ac 1 -ar 16000 -b:a 32k work/audio_16k.mp3`).
2. **transcribe** — same as podcast-shorts (key in `$ELEVENLABS_API_KEY` or
   `~/.elevenlabs_key`). Single narrator → expect a handful of huge turns;
   the word timestamps are what matter.
3. **sentences** writes `work/sentences.txt` — one timestamped sentence per
   line. Read it *in full* for the editorial pass.
4. **shotmap** classifies every 2s as `head` (talking head) or `scene`
   (parallax art) by frame-diff against reference talking-head frames, then
   refines each boundary to 0.25s. **You supply the refs**: extract ~15
   frames across the video, look at them, and pass 3 timestamps that are
   clearly the talking head (e.g. `120,240,480`). Sanity-check the printed
   map: it should alternate head/scene every ~20-30s in sync with the
   script beats; diff stats should show clear separation around the 25.0
   threshold.
5. **render** cuts `clips.json`, treating each span by type:
   - `head` → center crop 608x1080 → 1080x1920 (narrator is framed
     dead-center in the house style; if not, adjust the crop x in the
     script).
   - `scene` → full-width letterbox over a darkened blurred fill, so the
     art survives intact.
   - Karaoke captions (white → yellow fill, ≤3 words/line, DejaVu Sans)
     from the word timestamps, remapped onto the output timeline across
     reordered segments; audio loudnorm to −14 LUFS.

After rendering: extract 2–3 frames per clip and *look* at them (crop
framing, captions inside safe area, scene art not cropped), confirm every
duration is <60s with ffprobe.

## The editorial pass (the judgment step)

`clips.json` format: `assets/clips_template.json`. Ask the user how many
clips (default 8-9). Same selection rules as podcast-shorts (novel,
self-contained, one idea, <60s hard limit) plus:

- **Punchline-first + loop seam** (non-negotiable house rule, see the
  hook-first-looping-shorts memory): segment 1 is the punchline/thesis
  line pulled from wherever it occurs; the explanation follows; the final
  segment's last sentence must flow naturally back into the hook when the
  video loops. Best seam: end on the setup sentence that originally
  preceded the hook.
- Segments are raw `[start, end]` second pairs cut at sentence boundaries
  from `sentences.txt`. Mid-sentence hook starts are fine — snap to an
  exact word `start` from `work/transcript_raw.json` and begin ~0.04s
  before it.
- Record each clip's hook + loop seam in `CLIPS.md` for the user's review;
  re-cutting one clip is cheap (`render "<ep>" <slug>`).
- If the source was scripted, read the episode's `script.md` too — the
  written punchlines tell you where the hooks are.

## Fixing common issues

- Concat SAR mismatch errors → every span chain must end `setsar=1`
  (already handled; keep it if editing filters).
- Captions touching frame edge → lower fontsize / max words per line in
  the ASS constants.
- Shotmap misclassifies a span (e.g. a scene with muted colors close to
  the head backdrop) → hand-edit `work/shotmap_fine.json`, delete nothing,
  re-run render.
- A clip needs a different treatment for one span (e.g. crop a scene to
  its focal point instead of letterboxing) → add a manual override in the
  clip entry and extend the script; don't fight the classifier.
