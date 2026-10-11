"""Calibrate per-scene time scale so each scene's ANIMATION fills its narration.

Measure with holds disabled (RSI_NOHOLD=1). Measuring the rendered total is
useless: Timed.hold() pads every scene to the narration length, so the total always
equals the narration no matter how much of the scene is a frozen final frame. That
blind spot let S1/S2/S4 sit static for 28-41% of their runtime while calibration
reported a perfect match. Targeting the animated part makes tscale absorb the
slack as pacing instead of dead air.

Writes scenes/tscale.json, which rsi.py loads at import.

Usage: uv run --python 3.11 --with manim python calibrate.py
"""
import glob
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCENES = os.path.join(HERE, "scenes")
DUR = os.path.join(HERE, "audio", "durations.json")
TS_FILE = os.path.join(SCENES, "tscale.json")

MAP = {"S0": "0", "S1": "1", "S2": "2", "S3": "3", "S4": "4", "S5": "5"}

# Seconds of the narration that the final frame is allowed to sit alone. A scene
# whose animation runs right up to the last word ends on a hard cut; this reserves a
# short tail so the closing image lands and holds for a beat.
TAIL = 3.0


def narration():
    raw = json.load(open(DUR)) if os.path.exists(DUR) else {}
    return {k: float(raw.get(v, 0)) for k, v in MAP.items()}


def current_scales():
    src = open(os.path.join(SCENES, "rsi.py"), encoding="utf-8").read()
    out = {}
    for m in re.finditer(r"class (S\d)\(Timed\):\n(?:.*\n)*?\s+tscale = ([\d.]+)", src):
        out[m.group(1)] = float(m.group(2))
    return out


def render(scene):
    # RSI_NOHOLD=1 makes Timed.hold() a no-op, so the measured duration is the
    # animated part only -- the thing we actually want to stretch to the narration.
    subprocess.run(
        ["uv", "run", "--python", "3.11", "--with", "manim", "manim", "-ql",
         "--format=mp4", "-o", f"cal_{scene}", "rsi.py", scene],
        cwd=SCENES, env=dict(os.environ, RSI_NOHOLD="1"), check=False,
        stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    # rsi.py pins config.frame_rate = 30, so -ql writes to 480p30 (not 480p15).
    # Glob instead of hardcoding the resolution directory.
    hits = glob.glob(os.path.join(SCENES, "media", "videos", "rsi", "*",
                                  f"cal_{scene}.mp4"))
    if not hits:
        print(f"    (no output for {scene}; check the manim log)", flush=True)
        return None
    path = max(hits, key=os.path.getmtime)
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", path]).decode().strip()
    return float(out)


def main():
    narr = narration()
    scales = current_scales()
    if os.path.exists(TS_FILE):
        scales.update(json.load(open(TS_FILE)))
    cal = {}
    for scene in [s for s in ["S0", "S1", "S2", "S3", "S4", "S5"]
                  if not sys.argv[1:] or s in sys.argv[1:]]:
        want = narr.get(scene, 0.0)
        if want <= 0:
            print(f"{scene}: no narration duration yet, skip")
            continue
        measured = render(scene)
        if not measured:
            print(f"{scene}: render failed")
            continue
        target = max(1.0, want - TAIL)
        factor = target / measured
        new = round(scales.get(scene, 1.0) * factor, 4)
        cal[scene] = new
        # `slack` is how far the animated part falls short of the narration. Calibration
        # absorbs slack by slowing the animation, so what matters is the STRETCH this
        # scene needs: 1.0 = the authored pace is already right, 1.5 = every step drags.
        # A big stretch means the scene is mostly a frozen frame and needs more
        # animation, not a bigger tscale.
        slack = want - measured
        stretch = want / max(measured, 1e-9)
        if measured <= 0.5 * want:
            flag = (f"  <-- STRETCH {stretch:.2f}x: needs ~{target - measured:.0f}s more "
                    f"animation, not a bigger tscale")
        elif stretch > 1.25:
            flag = f"  <-- stretch {stretch:.2f}x: consider more animation"
        elif stretch < 0.90:
            flag = f"  <-- {measured - target:.0f}s over target: trim authored steps"
        else:
            flag = ""
        print(f"{scene}: anim {measured:6.1f}s  narr {want:6.1f}s  slack {slack:5.1f}s  "
              f"stretch {stretch:4.2f}x  tscale {scales.get(scene)} -> {new}{flag}")
    merged = dict(scales)
    merged.update(cal)
    json.dump(merged, open(TS_FILE, "w"), indent=1)
    print("wrote", TS_FILE, merged)


if __name__ == "__main__":
    main()
