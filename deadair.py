"""Measure animation vs dead air per scene.

For each rendered scene, sample frames, compute consecutive-frame change, and
report when the picture effectively stops changing. Everything after that is a
static hold: the scene is on screen but nothing is happening.

Usage: uv run --python 3.11 --with numpy --with pillow python deadair.py
"""
import subprocess, os, json
import numpy as np
from PIL import Image

SC = "scenes/media/videos/rsi/1080p30"
DUR = json.load(open("audio/durations.json"))
FPS = 2.0
W, H = 480, 270

print(f"{'scene':6s} {'video':>7s} {'narr':>7s} {'anim ends':>10s} {'dead air':>9s} {'%':>6s}")
print("-"*56)
for i in range(6):
    p = f"{SC}/S{i}.mp4"
    if not os.path.exists(p): continue
    d = float(subprocess.check_output(["ffprobe","-v","error","-show_entries",
        "format=duration","-of","csv=p=0",p]).decode().strip())
    n = int(d*FPS)
    tmp = "_da.png"
    subprocess.run(["ffmpeg","-y","-v","error","-i",p,"-vf",f"fps={FPS},scale={W}:{H}",
                    "-pix_fmt","rgb24",tmp], check=True)
    a = np.asarray(Image.open(tmp).convert("L"), dtype=np.int16)
    os.remove(tmp)
    n = a.shape[0]
    diffs = np.abs(np.diff(a, axis=0)).mean(axis=(1,2))
    # last sample where the picture changed appreciably
    idx = np.where(diffs > 0.35)[0]
    last = (idx[-1]+1)/FPS if len(idx) else 0.0
    narr = float(DUR[str(i)])
    dead = d - last
    print(f"S{i:<5d} {d:7.1f} {narr:7.1f} {last:10.1f} {dead:9.1f} {100*dead/d:5.1f}%")
