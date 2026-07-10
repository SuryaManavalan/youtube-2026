#!/usr/bin/env python3
"""Auto-classify freshly-pasted parallax plates in a scene folder and rename them.

Given a folder with two unclassified PNGs (e.g. the raw `Gemini_Generated_*.png`
foreground + background drops), decide which is the flat magenta chroma plate
(-> `<id>_fg.png`) and which is the inpainted background (-> `<id>_bg.png`),
rename them, and delete any Windows `:Zone.Identifier` sidecars.

    detect_plates.py --dir "path/to/scene folder" --id 3b
    detect_plates.py --dir . --id 0 --key magenta

Only touches PNGs that are NOT already named *_full/_fg/_bg. Refuses unless
exactly two such candidates are present (so it can't guess wrong on a messy dir).
"""
import argparse
import glob
import os
import numpy as np
from PIL import Image


def magenta_fraction(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(np.float32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]
    m = (R + B) / 2.0 - G
    return float((m > 150).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--id", required=True, help="scene id, e.g. 0, 3b, 6a")
    ap.add_argument("--key", default="magenta", choices=["magenta"])
    args = ap.parse_args()

    # clean sidecars
    for z in glob.glob(os.path.join(args.dir, "*:Zone.Identifier")):
        os.remove(z)

    cands = [p for p in sorted(glob.glob(os.path.join(args.dir, "*.png")))
             if not os.path.basename(p).lower().rsplit(".", 1)[0]
             .endswith(("_full", "_fg", "_bg"))]
    if len(cands) != 2:
        raise SystemExit(f"expected exactly 2 unclassified PNGs, found {len(cands)}: "
                         + ", ".join(os.path.basename(c) for c in cands))

    scored = sorted(cands, key=magenta_fraction, reverse=True)
    fg_src, bg_src = scored[0], scored[1]
    fg_dst = os.path.join(args.dir, f"{args.id}_fg.png")
    bg_dst = os.path.join(args.dir, f"{args.id}_bg.png")
    os.replace(fg_src, fg_dst)
    os.replace(bg_src, bg_dst)
    print(f"FG (magenta {magenta_fraction(fg_dst):.0%}): {os.path.basename(fg_src)} -> {os.path.basename(fg_dst)}")
    print(f"BG (magenta {magenta_fraction(bg_dst):.0%}): {os.path.basename(bg_src)} -> {os.path.basename(bg_dst)}")


if __name__ == "__main__":
    main()
