"""Detect content touching the frame edges.

Samples frames, estimates the true background from the frame corners (H.264/yuv420p
shifts #0b0f19 slightly, so a hardcoded colour creates false positives), then measures
the ink bounding box. Anything inside MARGIN px of an edge risks being cut off.

Usage: uv run --python 3.11 --with numpy --with pillow python edgeaudit.py <video> [margin] [thresh]
"""
import subprocess, sys, os
import numpy as np
from PIL import Image

video = sys.argv[1]
margin = int(sys.argv[2]) if len(sys.argv) > 2 else 10
thresh = int(sys.argv[3]) if len(sys.argv) > 3 else 60
W, H = 1920, 1080

dur = float(subprocess.check_output(
    ["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",video]
).decode().strip())
times = [round(x,1) for x in np.arange(0.5, dur-0.2, 1.0)]

bad, tmp = [], "_ea.png"
for t in times:
    subprocess.run(["ffmpeg","-y","-v","error","-ss",str(t),"-i",video,
                    "-frames:v","1","-vf",f"scale={W}:{H}","-pix_fmt","rgb24",tmp],
                   check=True)
    a = np.asarray(Image.open(tmp).convert("RGB")).astype(np.int16)
    patch = np.concatenate([a[0:14,0:14].reshape(-1,3), a[0:14,-14:].reshape(-1,3),
                            a[-14:,0:14].reshape(-1,3), a[-14:,-14:].reshape(-1,3)])
    bg = np.median(patch, axis=0)
    ink = (np.abs(a-bg).sum(axis=2) > thresh)
    if ink.sum() < 40:            # essentially the empty frame
        continue
    ys, xs = np.where(ink)
    l, r, tp, bt = int(xs.min()), int(W-1-xs.max()), int(ys.min()), int(H-1-ys.max())
    touch = [n for n,d in (("L",l),("R",r),("T",tp),("B",bt)) if d < margin]
    if touch:
        bad.append((t, touch, l, r, tp, bt))
if os.path.exists(tmp): os.remove(tmp)

if not bad:
    print(f"OK: no content within {margin}px of any edge across {len(times)} frames")
else:
    # collapse consecutive timestamps into spans
    spans, cur = [], [bad[0]]
    for row in bad[1:]:
        if row[0]-cur[-1][0] <= 1.01 and row[1] == cur[-1][1]: cur.append(row)
        else: spans.append(cur); cur=[row]
    spans.append(cur)
    print(f"{len(spans)} span(s) with content near an edge (margin {margin}px, {len(bad)}/{len(times)} frames):")
    for sp in spans:
        t0, t1 = sp[0][0], sp[-1][0]
        edges = ",".join(sp[0][1])
        mn = [min(x[i+2] for x in sp) for i in range(4)]
        print(f"  {t0:6.1f}-{t1:6.1f}s  {edges:9s} "
              f"worst margins L{mn[0]} R{mn[1]} T{mn[2]} B{mn[3]}")
