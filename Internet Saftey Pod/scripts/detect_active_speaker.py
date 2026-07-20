#!/usr/bin/env python3
"""Scan the OBS Discord recording at 1fps and detect which tile has the
green active-speaker border. Analyzes a full-resolution 12px-wide vertical
strip through the tiles' left borders (x 450-462) so the ~2px border
survives. Writes CSV: t_seconds,top,bottom.

Usage: python3 detect_active_speaker.py <input.mp4> <out.csv>
"""
import subprocess
import sys

import numpy as np

X0, XW = 450, 12          # strip covering left border of both tiles
TOP_Y = (115, 616)        # top tile y-range at full res
BOT_Y = (626, 1127)
H = 1200


def main(inp, out):
    proc = subprocess.Popen(
        [
            "ffmpeg", "-v", "error", "-i", inp,
            "-vf", f"fps=1,crop={XW}:{H}:{X0}:0",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
        ],
        stdout=subprocess.PIPE,
    )
    frame_bytes = XW * H * 3
    rows = []
    t = 0
    while True:
        buf = proc.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        img = np.frombuffer(buf, dtype=np.uint8).reshape(H, XW, 3).astype(int)
        r, g, b = img[..., 0], img[..., 1], img[..., 2]
        green = (g > 110) & (g > r + 35) & (g > b + 35)
        top = int(green[TOP_Y[0]:TOP_Y[1]].sum() > 40)
        bot = int(green[BOT_Y[0]:BOT_Y[1]].sum() > 40)
        rows.append(f"{t},{top},{bot}")
        t += 1
    proc.wait()
    with open(out, "w") as f:
        f.write("t,top,bottom\n" + "\n".join(rows) + "\n")
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
