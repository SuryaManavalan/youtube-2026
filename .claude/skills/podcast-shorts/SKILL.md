---
name: podcast-shorts
description: >-
  Turn a raw OBS screen recording of a 2-person Discord podcast call into
  vertical 1080x1920 YouTube Shorts (~8 clips, <60s each) with automatic
  camera work (full-screen active speaker, stacked reactions), diarized
  word-accurate cuts, burned-in karaoke captions, and audio equalization. Use whenever a folder in this
  repo contains a raw Discord-call recording and the user wants shorts/clips
  cut from it. Triggers: "create clips", "make shorts from this recording",
  "cut up the podcast", "new podcast episode", a new folder with a RAW
  screen recording in it.
---

# Podcast → Shorts Pipeline

Everything runs through **one orchestrator**:

```
python3 .claude/skills/podcast-shorts/scripts/pipeline.py <command> "<episode-dir>"
```

`<episode-dir>` is the video's top-level folder (e.g. `"Internet Saftey Pod"`).
The raw recording can sit anywhere inside it (usually `RAW/`). All generated
state lives in `<episode-dir>/work/`, finished clips in `<episode-dir>/SHORTS/`.

**If you are ever unsure where you are, run `status`** — it prints exactly
which steps are done and the next command to run:

```
python3 .claude/skills/podcast-shorts/scripts/pipeline.py status "Ep Folder"
```

## The five steps

Run them in order. Every step is idempotent (safe to re-run; finished work is
skipped). Long steps (`transcribe`, `analyze`, `render`) are worth running in
the background.

| # | Command | What it does | Needs |
|---|---------|--------------|-------|
| 1 | `init` | finds the video, probes it, extracts mono audio | a video file in the folder |
| 2 | `transcribe` | ElevenLabs Scribe, diarized, word timestamps → `work/transcript_turns.txt` | API key (see below) |
| 3 | `analyze` | auto-detects the two camera tiles from Discord's green active-speaker border, maps `speaker_0/1` → tiles, measures per-speaker loudness for mic equalization | steps 1–2 |
| 4 | *(you)* write `<episode-dir>/clips.json` | **the editorial step — see below** | step 3 |
| 5 | `edl` then `render` | snaps cuts to word boundaries (fix any printed PROBLEMS, rerun), renders the Shorts with burned-in word-timed karaoke captions (white → yellow fill; lower third on solo shots, at the cam seam on stacked so no face is covered) | step 4 |

API key: `$ELEVENLABS_API_KEY` or `~/.elevenlabs_key`. If neither exists, ask
the user for the key, save it to `~/.elevenlabs_key` (chmod 600).

Sanity checks worth doing: after `analyze`, confirm the printed speaker-map
confidence is high (it warns below 80%); after `render`, extract 2–3 frames
from one output with ffmpeg and look at them (tile framing, no green border,
captions readable and not covering a face), and confirm durations with
ffprobe.

## Step 4: the editorial pass (the part that needs judgment)

Read `work/transcript_turns.txt` **in full** — never skim, the gold is in
throwaway lines. Then write `<episode-dir>/clips.json`
(format: `assets/clips_template.json` next to this file).

Ask the user how many clips they want (default 8). Selection criteria:

- **Novel, self-contained, engaging.** Each clip must make complete sense to
  a stranger with zero context. If a moment needs setup, *build* the setup:
  you may reorder dialogue and pull a thesis line from minutes away — the
  word-accurate cutter makes invisible joins.
- **<60s hard limit** (the `edl` step warns), ~30–45s ideal. One idea per
  clip. Trim filler turns ("yeah", "mm-hmm") by simply not including them.
- Prefer: strong analogies, coined phrases, punchlines with reactions, hot
  takes, "wait, what?" facts, self-referential/meta moments. Skip: inside
  references that can't be explained in-clip, and moments whose only energy
  is context you'd have to add.
- **Punchline-first + loop seam.** Open the clip with the punchline/thesis
  line itself, pulled from wherever it chronologically occurs — then let the
  explanation follow. Because Shorts/Reels/TikTok loop, choose an ending
  line that flows naturally back into the relocated hook: the viewer hits
  the end, the video restarts, and the explanation now *lands on* the hook
  it was building to. Best seams: end on the setup sentence that originally
  preceded the hook (e.g. end "…it needs a cup." → loop to hook "the agent
  is the cup, but a cup shaped like hands"). Never end on a trailing
  "you know?".
- Check the episode folder or ask for topic-sensitivity concerns (e.g. avoid
  leading with monetization-hostile content).

Shot grammar (`shot` field):
- `solo` — default; full-screen whoever is talking.
- `stacked` — both cams; use for punchlines, reactions, and rapid banter.
- `speaker: "any"` — keeps both speakers' words in a time range (banter);
  always pairs with `stacked`.

Write a `CLIPS.md` in the episode folder summarizing each clip (title, why it
works, the excerpt) so the user can review the plan — show it to them before
or right after rendering; re-cutting any single clip is cheap:
edit `clips.json` → `edl` → `render <ep> <slug>`.

## Fixing common issues

- `edl` prints `no words in range` → the time range/speaker in clips.json is
  wrong; open transcript_turns.txt at that timestamp and correct it.
- Clip over 60s → drop or tighten segments in clips.json, rerun `edl`.
- Face off-center in solo shots → add `"face_x": {"A": 0.45}` (fraction of
  tile width where the face center sits) to `work/episode.json`, re-render.
- Speaker map looks wrong (voices swapped) → swap values in
  `work/episode.json` → `speaker_tile`, re-render.
- Layout detection fails → the recording may lack the green border (Discord
  Streamer Mode still shows it; but a non-Discord recording won't). Measure
  tile rects manually from a frame and write `tiles`/`layout` into
  `work/episode.json`, then continue with `analyze`.

## Assumptions / limits

- 2-person call, one camera tile each, fixed layout (Discord grid), tiles
  stacked vertically or side-by-side; any resolution.
- Output: 1080x1920 @30fps, h264 CRF 19, audio loudnorm to −14 LUFS with
  per-speaker mic-imbalance gain applied per segment.
- First built for "Internet Saftey Pod" (2026-07); that episode's original
  one-off scripts in its `scripts/` folder are superseded by this skill.
