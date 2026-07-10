# youtube-2026

Production repo for a series of illustrated video essays — script, scene art, and the
tooling that turns still wojak/pepe-style scenes into subtle **2.5D parallax** motion
clips.

## Videos

| Folder | Working title | Thumbnail hook |
|--------|---------------|----------------|
| [`Cybernetics/`](Cybernetics/) | *Transhumanism is already here* | How cybernetic implants affect mental health |
| [`AI Agent Meta-Computation/`](AI%20Agent%20Meta-Computation/) | *AI Agent Meta-Computation* | AI Souls and Spirit |

Each video folder holds:

```
planning.md        # intent + brain-dump
script.md          # (working script)
scenes/
  STYLE_REFERENCE.md      # shared art-direction for the whole set
  PARALLAX_PROMPTS.md     # per-image foreground/background split prompts
  N. TITLE (hint)/        # one folder per scene
    N. TITLE (hint).md     # spoken-prose narration + [CAM]/[CLIP]/[SFX]/[WOJAK] cues
    N_full.png             # original full illustration
    N_fgsrc.png            # raw magenta foreground plate (chroma-key source)
    N_fg.png               # keyed transparent foreground
    N_bg.png               # inpainted background plate
    N_parallax.mp4         # rendered motion clip  (gitignored — see below)
```

Scenes with multiple `[WOJAK]` images use `a/b/c` suffixes (`3a`, `3b`, `3c`).

## The parallax pipeline

A reusable Claude Code skill lives in
[`.claude/skills/parallax-scene/`](.claude/skills/parallax-scene/). It documents the
five-phase workflow (scene breakdown → split prompts → ingest/rename → chroma-key →
render) and ships the scripts:

- `scripts/detect_plates.py` — auto-classify a scene's two pasted plates (magenta =
  foreground) and rename them.
- `scripts/keychroma.py` — key the flat magenta plate to transparency (soft alpha +
  despill).
- `scripts/render_parallax.py` — render the clip. One virtual camera dollies + trucks;
  the foreground moves more than the background (real parallax). Sub-pixel affine
  sampling + a near-constant-velocity path keep it smooth.
- `scripts/process_scene.sh` — run all three in one call:

```bash
.claude/skills/parallax-scene/scripts/process_scene.sh "AI Agent Meta-Computation/scenes/0. COLD OPEN (the hook)" 0
```

**Requirements:** `python3` with `Pillow` + `numpy`, and `ffmpeg` on `PATH`.

## What's tracked vs ignored

Tracked: all text (scripts, scene narration, prompts, the skill) and the **source/plate
images** (`*_full.png`, `*_fgsrc.png`, `*_fg.png`, `*_bg.png`) — the generated art is
non-deterministic and can't be reproduced exactly, so it's version-controlled.

Ignored (see [`.gitignore`](.gitignore)): the rendered **`*_parallax.mp4`** clips (large,
and one command to rebuild from the tracked layers) and `*_keypreview.png` QA scratch. To
version the videos too, use [Git LFS](https://git-lfs.com/) rather than committing them
directly.
