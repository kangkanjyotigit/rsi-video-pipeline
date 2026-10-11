"""Measure ANIMATION-ONLY time per scene (holds disabled).

calibrate.py measures the rendered total, but Timed.hold() pads every scene to the
narration length, so the total always equals the narration and the measurement is
blind to how much of the scene is a frozen frame. This renders with RSI_NOHOLD=1
so hold() returns immediately, giving the true length of the animated part.

Usage: uv run --python 3.11 --with manim python animtime.py [S0 S1 ...]
"""
import glob, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCENES = os.path.join(HERE, "scenes")
DUR = os.path.join(HERE, "audio", "durations.json")
MAP = {"S0": "0", "S1": "1", "S2": "2", "S3": "3", "S4": "4", "S5": "5"}

want = json.load(open(DUR))
scenes = sys.argv[1:] or ["S0", "S1", "S2", "S3", "S4", "S5"]
print(f"{'scene':6s} {'anim':>7s} {'narr':>7s} {'slack':>7s} {'factor':>7s}")
print("-" * 40)
for sc in scenes:
    env = dict(os.environ, RSI_NOHOLD="1")
    subprocess.run(
        ["uv", "run", "--python", "3.11", "--with", "manim", "manim", "-ql",
         "--format=mp4", "-o", f"anim_{sc}", "rsi.py", sc],
        cwd=SCENES, env=env, check=False,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    hits = glob.glob(os.path.join(SCENES, "media", "videos", "rsi", "*",
                                  f"anim_{sc}.mp4"))
    if not hits:
        print(f"{sc}: render failed"); continue
    p = max(hits, key=os.path.getmtime)
    a = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of", "csv=p=0", p]).decode().strip())
    n = float(want[MAP[sc]])
    print(f"{sc:6s} {a:7.1f} {n:7.1f} {n-a:7.1f} {n/a:7.2f}")
