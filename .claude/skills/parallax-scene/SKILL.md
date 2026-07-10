---
name: parallax-scene
description: >-
  Produce the wojak/pepe video-essay scenes and their 2.5D parallax motion clips
  for the youtube-2026 projects — from scaffolding a brand-new video to rendering
  the final clips. Use when starting a new video, writing scene outlines in the
  Cybernetics scene format, generating foreground/background split prompts for image
  gen, chroma-keying magenta plates to transparency, or rendering subtle parallax
  video from a foreground+background pair. Triggers: "new video", "start a video",
  "parallax", "scene image", "foreground/background", "wojak scene", "make the clip
  move", "key the magenta".
---

# Parallax Scene Production

The end-to-end pipeline for the channel's illustrated video essays — from a new idea to
finished motion-parallax scenes. Built for the `youtube-2026` repo (Cybernetics, AI Agent
Meta-Computation, …). Every video lives in its own top-level folder with `planning.md`,
`script.md`, and a `scenes/` directory.

## The channel (voice & content)

These essays take a **familiar-ish modern topic** — internet culture, philosophy, computer
science, or a general interesting idea — and **reinterpret it through the creator's own
esoteric-but-grounded framework**. The register is **slightly humorous, genuinely
thought-provoking, esoteric yet modern and relevant**. Hold this voice when writing scripts
and scenes:

- **A novel lens, stated as a lens.** Reframe something the audience half-knows into one
  clear thesis, and openly flag it as a personal interpretation, not institutional fact.
- **Escalating zoom-out arc.** Each beat is more abstract / larger-scale than the last
  (concrete → cosmic). Open on a provocative, thumbnail-worthy hook; close on a quotable
  button that ties back to it.
- **Earn the wild claims.** Front-load the framing that gives you the right to the strange
  ideas later; then go as far-out as the idea allows.
- **Humor is dry and embedded**, never a caption-level punchline — in the phrasing and in
  the background gags of the art (see `STYLE_REFERENCE.md`).
- **Grounded esoterica.** Bridge to real history/philosophy/CS; keep one foot in the
  concrete so the metaphysics lands as insight, not vibes.

## Naming conventions (do not deviate)

Each scene gets a folder inside `scenes/`, named `N. TITLE (hint)` (sub-scenes
`Na. Subtitle`). Inside a scene folder:

| file | meaning |
|------|---------|
| `<id>_full.png` | the original full illustration |
| `<id>_fgsrc.png` | raw magenta foreground plate (key source; keep for re-tuning) |
| `<id>_fg.png` | foreground plate — transparent RGBA after keying |
| `<id>_bg.png` | background plate — key subjects removed + inpainted |
| `<id>_parallax.mp4` | the rendered motion clip |
| `<id>_keypreview.png` | QA composite (fg over bg); delete before publishing |

`<id>` matches the scene number, with `a/b/c` suffixes when a scene has multiple
`[WOJAK]` images (e.g. `3a`, `3b`, `3c`). The scene's `.md` also lives in the folder.

## The phases

### 0. Scaffold a new video — `scripts/new_video.sh`
Spin up a new video folder matching the channel layout (planning + script + a `scenes/`
with the canonical `STYLE_REFERENCE.md` and an empty `PARALLAX_PROMPTS.md`):
```
scripts/new_video.sh "Video Title" "THUMBNAIL TEXT" "Youtube Title"
```
Then fill `planning.md` (intent + brain-dump), holding the **voice** above, and proceed to
phase 1. Templates live in `assets/` (`planning_template.md`, `style_reference_template.md`,
`parallax_prompts_template.md`) — edit those to evolve the house defaults for all future
videos.

### 1. Scene breakdown (`scenes/<N>. …/<N>. ….md` + `STYLE_REFERENCE.md`)
Break the video's `planning.md` brain-dump into an escalating scene arc. Each scene
`.md` is spoken-prose narration with inline cues (`[CAM]`, `[CLIP]`, `[SFX]`,
`[FX]`, and `[WOJAK]` with a `^ |` attaching the visual to the line above).
Keep a `STYLE_REFERENCE.md` in `scenes/` describing the shared look. **Non-negotiable
style rules** (learned from the Cybernetics set):
- Dense, painterly, populated scenes with real environments — not characters on white.
- Meme faces (wojak/soyjak/npc/pepe) grafted onto realistically-drawn, clothed people.
- **Diegetic text only** (labels, signs, screens, name-tags). No floating captions —
  except deliberate infographic/taxonomy plates.
- Humor as embedded background gags, never caption-level punchlines.
- Consistent grade + one glowing energy accent that threads through every scene.

### 2. Split prompts (`scenes/PARALLAX_PROMPTS.md`)
For each `_full` image write TWO image-gen prompts (see `assets/split_prompt_template.md`).
The model can't segment reliably, so **name the specific foreground objects**.
- **Foreground**: "isolate ONLY [objects], everything else flat bright magenta `#FF00FF`."
- **Background**: "remove ONLY [objects], inpaint what's behind them, keep everything
  else EXACTLY the same."
Use **magenta**, not black — scenes are dark/teal and black blends into the subjects.
Both prompts must preserve kept-subject pixels exactly so the layers re-composite in
alignment. Flat 2D infographic scenes (taxonomy cards, diagram plates) can skip parallax.

### 3. Ingest & rename — `scripts/detect_plates.py`
After pasting the two generated plates into the scene folder:
```
python3 scripts/detect_plates.py --dir "scenes/0. COLD OPEN (the hook)" --id 0
```
Auto-classifies the magenta plate as `<id>_fg.png` and the other as `<id>_bg.png`,
and removes `:Zone.Identifier` sidecars. Refuses unless exactly two unclassified PNGs
are present.

### 4. Chroma-key the foreground — `scripts/keychroma.py`
Magenta → transparent, with a soft alpha ramp + despill (kills edge halos). Key
**from the raw plate to a distinct output** so the raw is preserved for re-tuning:
```
cp "<dir>/0_fg.png" "<dir>/0_fgsrc.png"          # keep the raw magenta plate
python3 scripts/keychroma.py "<dir>/0_fgsrc.png" "<dir>/0_fg.png" \
    --preview "<dir>/0_bg.png" "<dir>/0_keypreview.png"
```
Always eyeball the `_keypreview.png` at 100%: subjects intact, **no magenta rim on
edges** (esp. tops of heads), scene reconstructs in alignment. If a pink rim remains,
raise `--despill` (default 1.0) or lower `--hi`; if a subject color is being eaten,
raise `--lo/--hi`. Never key an already-keyed RGBA in place — re-key from `_fgsrc`.

### 5. Render the parallax clip — `scripts/render_parallax.py`
Each layer is a crop-window that both **dollies** (zoom) and **trucks** (slides its
center across the plate). The physics we honor (see the script header for the full
derivation): on a lateral camera move a nearer plane shifts *more* (ratio ≈ Z_bg/Z_fg)
— so **the background moves too, just slower; it is never locked** — and on a dolly the
nearer plane scales faster. So the foreground gets a wider center-travel *and* zoom
range than the background. Default is a cinematic **start zoomed-in on one side → pull
back + pan across** (both layers dolly out and truck the same direction, fg ~2× bg).
Smoothness = **sub-pixel affine sampling** (no whole-pixel jitter) + a **near-constant
velocity** path (small eased ends), so the camera reads as *already moving* — no
imperceptible crawl at the start.
```
python3 scripts/render_parallax.py "<dir>/0_bg.png" "<dir>/0_fg.png" \
    "<dir>/0_parallax.mp4" --seconds 30
```
Output: 1920×1080, 30 fps, H.264/yuv420p. Useful flags:
- `--bg-zoom 1.14 1.05 --fg-zoom 1.22 1.07` — dolly range per layer (start→end). Make
  zoom *increase* to dolly IN instead of out.
- `--fg-cx 0.42 0.58 --bg-cx 0.46 0.54` — center-x path (0..1) start→end; fg range wider
  than bg = parallax. Flip the pair to pan the other way. `--fg-cy/--bg-cy` for vertical.
- `--ramp 0.08` — eased fraction each end; small = already-moving camera (raise for a
  gentler start/stop). `--loop` — seamless out-and-back; `--seconds/--fps/--size`.

Centers auto-clamp so the frame never slides off the plate. Calmer → shrink the cx/zoom
spreads; more active → widen them. Foreground plate should be full-res (low-res softens).

## One-shot per scene — `scripts/process_scene.sh`
Phases 3–5 in one call (run after the two plates are pasted in):
```
scripts/process_scene.sh "scenes/0. COLD OPEN (the hook)" 0
scripts/process_scene.sh "scenes/3. THE FUNCTION → THE FLUID" 3b 30 --loop
```

## Requirements
`python3` with `Pillow` + `numpy`, and `ffmpeg` on PATH. Rendering 30 s @ 30 fps
takes ~1–2 min; long renders self-background — wait on the output file, don't poll.

## Gotchas
- **Pan + zoom-out reversal (fixed in-script):** zooming out shrinks the pan headroom,
  so a pan target that's valid at the zoomed-in start can overshoot at the zoomed-out
  end; the per-frame clamp then drags the center back, reversing motion in the last few
  seconds. `render_parallax.py` clamps pan targets to the tightest (min-zoom) headroom up
  front to keep the center path monotonic. If you widen `--pan`/cx ranges or deepen the
  zoom-out, keep the cx endpoints inside `[1/(2·min_zoom), 1-1/(2·min_zoom)]` or the
  clamp will silently eat the excess (no reversal, just less pan than you asked for).
- Foreground plates sometimes bake a faint key-color wash into transition zones
  (AI blending subjects into the magenta). It moves with the FG layer so it won't
  seam, but regenerate that plate if you want it perfectly clean.
- Keep `<id>_full.png` forever — it's the re-split source of truth.
- Scene folders contain spaces and Unicode (`→`, `↔`, `'`); always quote paths.
