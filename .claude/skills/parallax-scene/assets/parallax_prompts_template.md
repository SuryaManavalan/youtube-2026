# Parallax Foreground / Background Prompts

Two prompts per scene image (one FOREGROUND, one BACKGROUND). Fill one block per
`[WOJAK]` image once the scenes exist. See the reusable pattern in the skill's
`assets/split_prompt_template.md`, and the finished example in another video's
`scenes/PARALLAX_PROMPTS.md`.

**Chroma key:** foreground plates use flat **bright magenta `#FF00FF`** (dark/teal scenes
— black would blend into subjects). Both prompts must preserve kept-subject pixels
EXACTLY so the layers re-composite in alignment. Flat infographic plates can skip parallax.

---

## <N. SCENE TITLE>

**FOREGROUND** (→ `<id>_fg.png`, later keyed transparent)
> Isolate ONLY these foreground elements from this image, keeping them EXACTLY as they
> appear (same position, scale, colors, line art, lighting): [LIST THE SPECIFIC NEAR/MAIN
> SUBJECTS]. Erase everything else and replace the entire rest of the image with a solid
> flat bright magenta `#FF00FF` background for chroma keying. Keep clean hard edges. Do
> not add anything. Preserve their original pixels precisely for perfect re-alignment.

**BACKGROUND** (→ `<id>_bg.png`)
> Generate the background plate: remove ONLY [SAME SUBJECTS]. Realistically paint back in
> what is behind them — continue the [FLOOR/WALL/CROWD/SCENERY] seamlessly. Everything
> else must stay EXACTLY the same: [KEY ELEMENTS THAT MUST NOT CHANGE]. Do not move or
> restyle anything. Same scene, just with those subjects absent.
