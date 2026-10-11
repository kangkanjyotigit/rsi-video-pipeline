"""Identify what is touching a frame edge, by colour, over time.

Usage: edgewhat.py <video> <edge L|R|T|B> <t1> [t2 ...]
"""
import subprocess, sys, os
import numpy as np
from PIL import Image

video, edge = sys.argv[1], sys.argv[2].upper()
times = [float(x) for x in sys.argv[3:]]
W, H = 1920, 1080
NAMED = {"red":(232,85,90),"green":(78,203,113),"cyan":(88,196,221),"blue":(59,139,232),
         "yellow":(255,213,74),"orange":(255,140,66),"purple":(180,140,232),
         "grey":(140,147,168),"white":(242,242,242)}
tmp="_ew.png"
for t in times:
    subprocess.run(["ffmpeg","-y","-v","error","-ss",str(t),"-i",video,"-frames:v","1",
                    "-vf",f"scale={W}:{H}","-pix_fmt","rgb24",tmp],check=True)
    a=np.asarray(Image.open(tmp).convert("RGB")).astype(np.int16)
    patch=np.concatenate([a[0:14,0:14].reshape(-1,3),a[0:14,-14:].reshape(-1,3),
                          a[-14:,0:14].reshape(-1,3),a[-14:,-14:].reshape(-1,3)])
    bg=np.median(patch,axis=0)
    ink=(np.abs(a-bg).sum(axis=2)>60)
    for name,px in [("L",(slice(None),slice(0,6))),("R",(slice(None),slice(W-6,W))),
                    ("T",(slice(0,6),slice(None))),("B",(slice(H-6,H),slice(None)))]:
        if name!=edge: continue
        band=ink[px]
        if band.sum()<3:
            print(f"  t={t:6.1f}s {edge}: clear"); continue
        ys,xs=np.where(band)
        if edge in ("L","R"): pos=(ys.min(),ys.max()); ax="y"
        else: pos=(xs.min(),xs.max()); ax="x"
        cols=a[px][band]
        # nearest palette colour
        best=min(NAMED.items(), key=lambda kv: np.abs(cols.mean(0)-np.array(kv[1])).sum())
        print(f"  t={t:6.1f}s {edge}: {band.sum():4d}px  {ax}=[{pos[0]},{pos[1]}]  "
              f"meanRGB=({cols.mean(0)[0]:.0f},{cols.mean(0)[1]:.0f},{cols.mean(0)[2]:.0f}) ~{best[0]}")
if os.path.exists(tmp): os.remove(tmp)
