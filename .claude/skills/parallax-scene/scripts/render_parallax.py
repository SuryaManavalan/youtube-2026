#!/usr/bin/env python3
"""Render a smooth 2.5D parallax clip from a transparent FG plate over a BG plate.

Camera model: one virtual camera slowly pans (and slightly tilts) while doing a
gentle dolly-zoom. Both layers ride the SAME camera path, but the foreground pans
and zooms MORE than the background -- that depth-proportional difference is real
parallax, and reading as one camera move (rather than two sliding cutouts) is what
makes it feel natural.

The move is defined per layer as a crop-window that both ZOOMS (dolly) and slides its
CENTER across the plate (truck). Physics we honor:
  * Truck: nearer plane shifts more; ratio ~ Z_bg/Z_fg. So the background also moves,
    just slower -- it is never locked. (fg center travels ~2x the bg center.)
  * Dolly: nearer plane scales faster, so fg zoom range > bg zoom range.
Default is a cinematic "start zoomed-in on one side, pull back + pan across": both
layers dolly OUT and truck the same direction, foreground more.

Smoothness comes from two things:
  1. Sub-pixel sampling. Each frame is an affine warp (bicubic), so motion is
     continuous instead of snapping to whole pixels -- that pixel-snapping is what
     makes slow parallax look jittery.
  2. A near-constant velocity path (small eased ends via --ramp) so the camera reads
     as already in motion -- no imperceptible crawl at the start, no jerk at the ends.

    render_parallax.py BG.png FG.png OUT.mp4
        [--seconds 30] [--fps 30] [--size 1920x1080]
        [--bg-zoom 1.14 1.05] [--fg-zoom 1.22 1.07]
        [--bg-cx 0.46 0.54] [--fg-cx 0.42 0.58]       # center-x path (0..1), start->end
        [--bg-cy 0.49 0.51] [--fg-cy 0.46 0.54]       # center-y path
        [--ramp 0.08] [--loop] [--crf 18]

Center paths are normalized [0,1] on the plate and auto-clamped so the window never
slides off (as zoom->1 the center is forced toward 0.5 -- no headroom to pan when not
zoomed in). Give fg a wider cx/zoom range than bg for stronger parallax. Flip the cx
pairs to pan the other way; make zoom increase (e.g. 1.05->1.14) to dolly IN instead.
--loop makes an out-and-back path for a seamless loop. Requires ffmpeg on PATH.
"""
import argparse
import subprocess
from PIL import Image


def lerp(a, b, t):
    return a + (b - a) * t


def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def drive_path(n, ramp, loop):
    """Return n normalized positions in [0,1] with eased ends + constant-speed middle.
    If loop, the path goes 0 -> 1 -> 0 so first and last frames match seamlessly."""
    def eased_positions(count):
        # per-step velocity: ramp up over `ramp`, cruise, ramp down
        vel = []
        for i in range(count):
            t = i / (count - 1) if count > 1 else 0.0
            if t < ramp:
                v = smoothstep(t / ramp)
            elif t > 1 - ramp:
                v = smoothstep((1 - t) / ramp)
            else:
                v = 1.0
            vel.append(v)
        total = sum(vel) or 1.0
        acc, pos = 0.0, []
        for v in vel:
            pos.append(acc / total)
            acc += v
        pos.append(1.0)          # ensure endpoint hits exactly 1
        return pos[:count] if count > 1 else [0.0]

    if not loop:
        return eased_positions(n)
    half = eased_positions(n // 2 + 1)          # 0 -> 1
    back = half[::-1]                            # 1 -> 0
    path = half + back[1:]
    # pad/trim to exactly n
    if len(path) < n:
        path += [path[-1]] * (n - len(path))
    return path[:n]


def warp(src, out_w, out_h, zoom, cx, cy):
    """Affine sub-pixel warp: sample a (W/zoom x H/zoom) window whose CENTER sits at
    normalized (cx,cy) in [0,1] of the plate, scaled up to out_w x out_h. The center
    is clamped so the window always stays fully inside the plate (as zoom -> 1 the
    window fills the plate and the center is forced toward 0.5 -- physically correct:
    no headroom to pan when you're not zoomed in)."""
    W, H = src.size
    win_w, win_h = W / zoom, H / zoom
    hx, hy = (win_w / 2.0) / W, (win_h / 2.0) / H      # normalized half-window
    cx = min(1.0 - hx, max(hx, cx))
    cy = min(1.0 - hy, max(hy, cy))
    left = cx * W - win_w / 2.0
    top = cy * H - win_h / 2.0
    a = win_w / out_w
    e = win_h / out_h
    return src.transform((out_w, out_h), Image.AFFINE, (a, 0, left, 0, e, top),
                         resample=Image.BICUBIC)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("bg"); ap.add_argument("fg"); ap.add_argument("out")
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--size", default="1920x1080")
    # Default move: start zoomed-in on the left, TRUCK right + DOLLY out. Foreground
    # trucks/zooms ~2x the background (parallax). Same direction on both = one camera.
    ap.add_argument("--bg-zoom", type=float, nargs=2, default=[1.14, 1.05])
    ap.add_argument("--fg-zoom", type=float, nargs=2, default=[1.22, 1.07])
    ap.add_argument("--bg-cx", type=float, nargs=2, default=[0.46, 0.54], help="bg center-x path 0..1")
    ap.add_argument("--fg-cx", type=float, nargs=2, default=[0.42, 0.58], help="fg center-x path 0..1")
    ap.add_argument("--bg-cy", type=float, nargs=2, default=[0.49, 0.51], help="bg center-y path 0..1")
    ap.add_argument("--fg-cy", type=float, nargs=2, default=[0.46, 0.54], help="fg center-y path 0..1")
    ap.add_argument("--ramp", type=float, default=0.08,
                    help="eased fraction each end; small = already-moving camera, no crawl")
    ap.add_argument("--loop", action="store_true")
    ap.add_argument("--crf", type=int, default=18)
    args = ap.parse_args()

    out_w, out_h = (int(x) for x in args.size.lower().split("x"))
    n = int(args.seconds * args.fps)
    bg = Image.open(args.bg).convert("RGB")
    fg = Image.open(args.fg).convert("RGBA")
    path = drive_path(n, args.ramp, args.loop)

    # Clamp the pan targets to the TIGHTEST headroom over the whole move (the min-zoom
    # frame). Otherwise, when the camera zooms out, a pan target can overshoot the
    # shrinking headroom, the per-frame clamp engages, and its inward-moving boundary
    # drags the center back the other way near the end -- a jarring reverse. Pinning the
    # endpoints inside the intersection range keeps the center path monotonic.
    def safe_targets(zoom_pair, cx_pair, cy_pair):
        h = 1.0 / (2.0 * min(zoom_pair))            # half-window at min zoom (x and y equal)
        cl = lambda v: min(1.0 - h, max(h, v))
        return (cl(cx_pair[0]), cl(cx_pair[1])), (cl(cy_pair[0]), cl(cy_pair[1]))

    bg_cx, bg_cy = safe_targets(args.bg_zoom, args.bg_cx, args.bg_cy)
    fg_cx, fg_cy = safe_targets(args.fg_zoom, args.fg_cx, args.fg_cy)

    proc = subprocess.Popen([
        "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
        "-s", f"{out_w}x{out_h}", "-r", str(args.fps), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "medium", "-crf", str(args.crf),
        "-pix_fmt", "yuv420p", "-movflags", "+faststart", args.out,
    ], stdin=subprocess.PIPE)

    for i in range(n):
        d = path[i]                       # 0..1 eased camera progress (near-constant vel)
        bframe = warp(bg, out_w, out_h, lerp(*args.bg_zoom, d),
                      lerp(*bg_cx, d), lerp(*bg_cy, d))
        fframe = warp(fg, out_w, out_h, lerp(*args.fg_zoom, d),
                      lerp(*fg_cx, d), lerp(*fg_cy, d))
        frame = bframe.convert("RGBA")
        frame.alpha_composite(fframe)
        proc.stdin.write(frame.convert("RGB").tobytes())
        if i % 90 == 0:
            print(f"frame {i}/{n}", flush=True)

    proc.stdin.close()
    proc.wait()
    print("done ->", args.out)


if __name__ == "__main__":
    main()
