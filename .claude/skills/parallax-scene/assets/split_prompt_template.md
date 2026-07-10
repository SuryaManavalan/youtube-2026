# FG / BG Split-Prompt Template

Fill the `[BRACKETS]` per image. Pass each prompt + the `_full` image into the
generator (one run for FG, one for BG). Keep the two rules verbatim — they're what
makes the layers re-composite in alignment.

## FOREGROUND (→ `<id>_fg.png`, later keyed transparent)
> Isolate ONLY these foreground elements from this image, keeping them EXACTLY as
> they appear (same position, scale, colors, line art, lighting): [LIST THE SPECIFIC
> NEAR/MAIN SUBJECTS — e.g. "the central front-row audience group and the crouching
> janitor with the mop"]. Erase everything else and replace the entire rest of the
> image with a solid flat bright magenta `#FF00FF` background for chroma keying. Keep
> clean hard edges around the isolated subjects. Do not add anything. Preserve their
> original pixels precisely so this layer aligns perfectly when composited back over
> the original.

## BACKGROUND (→ `<id>_bg.png`)
> Generate the background plate of this image: remove ONLY [SAME SUBJECTS AS ABOVE].
> Realistically paint back in whatever is behind them — continue the [FLOOR / WALL /
> CROWD / SCENERY] seamlessly. Everything else must stay EXACTLY the same: [LIST KEY
> ELEMENTS THAT MUST NOT CHANGE — signage, distant figures, lighting, screens]. Do
> not move or restyle anything. Same scene, just with those subjects absent.

## Picking the foreground
- Foreground = the nearest / most prominent actors that should "pop" over the
  receding background. Distant crowds and environment stay in the background.
- If actors are scattered around a room, it's fine to take them all as foreground.
- Chroma color: **magenta `#FF00FF`** by default (dark/teal scenes). Use black only
  if a subject is itself strongly magenta.
- Flat 2D infographics (taxonomy cards, diagram plates): parallax optional — either
  skip, or split the central figure from the labels for a faint float.
