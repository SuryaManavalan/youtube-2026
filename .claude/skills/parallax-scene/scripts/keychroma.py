#!/usr/bin/env python3
"""Chroma-key a flat magenta (or green) plate to transparency.

Produces an RGBA PNG with the flat key color removed via a soft alpha ramp,
plus a light despill pass so anti-aliased edges don't keep a colored halo.

    keychroma.py IN.png OUT.png [--key magenta|green] [--lo 60] [--hi 150]
                 [--despill 0.5] [--preview BG.png PREVIEW_OUT.png]

Defaults are tuned for the bright-magenta (#FF00FF) chroma plates used by the
parallax-scene pipeline. Foreground subjects there are desaturated grey with
occasional blue phone-glow, all far from magenta in hue, so the key is clean.
"""
import argparse
import numpy as np
from PIL import Image


def key_metric(R, G, B, key):
    """High where the pixel matches the key color, ~0 elsewhere."""
    if key == "magenta":          # pure magenta = (255,0,255): red&blue high, green low
        return (R + B) / 2.0 - G
    elif key == "green":          # pure green = (0,255,0): green high, red&blue low
        return G - (R + B) / 2.0
    raise ValueError(f"unknown key {key!r}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inp")
    ap.add_argument("outp")
    ap.add_argument("--key", default="magenta", choices=["magenta", "green"])
    ap.add_argument("--lo", type=float, default=60.0, help="metric<=lo -> fully opaque")
    ap.add_argument("--hi", type=float, default=150.0, help="metric>=hi -> fully transparent")
    ap.add_argument("--despill", type=float, default=1.0, help="0..1 edge color-cast removal")
    ap.add_argument("--preview", nargs=2, metavar=("BG", "OUT"),
                    help="composite result over BG and save OUT (QA)")
    args = ap.parse_args()

    img = Image.open(args.inp).convert("RGB")
    a = np.asarray(img).astype(np.float32)
    R, G, B = a[..., 0], a[..., 1], a[..., 2]

    m = key_metric(R, G, B, args.key)
    alpha = np.clip((args.hi - m) / (args.hi - args.lo), 0.0, 1.0)

    # despill: pull the key color's cast out of edge pixels
    excess = np.clip(m, 0.0, None) * args.despill
    if args.key == "magenta":
        R, B = R - excess, B - excess
    else:  # green
        G = G - excess
    rgb = np.clip(np.stack([R, G, B], axis=-1), 0, 255)

    out = np.dstack([rgb, alpha * 255.0]).astype(np.uint8)
    Image.fromarray(out, "RGBA").save(args.outp)
    print(f"{args.outp}: transparent {(alpha < 0.05).mean():.1%}, "
          f"opaque {(alpha > 0.95).mean():.1%}")

    if args.preview:
        bg = Image.open(args.preview[0]).convert("RGBA").resize(img.size)
        comp = Image.alpha_composite(bg, Image.fromarray(out, "RGBA"))
        comp.convert("RGB").save(args.preview[1])
        print("preview ->", args.preview[1])


if __name__ == "__main__":
    main()
