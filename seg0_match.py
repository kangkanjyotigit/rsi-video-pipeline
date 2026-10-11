"""Regenerate seg0 until it matches the vocal profile of the already-synthesised
segments 1-5, so the opener does not sound like a different narrator.

Quota note: gemini-3.8-flash-tts allows 10 req/day/project; we have a couple left,
so this tries a small number of candidates and keeps the best.
"""
import re, wave, os
import numpy as np
import tts_multi as T

T.MODELS = ["gemini-3.8-flash-tts"]        # pin: same model as segs 1-5

def load(p):
    with wave.open(p) as w:
        d = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64)
        if w.getnchannels() == 2: d = d.reshape(-1, 2).mean(1)
        return d, w.getframerate()

def profile(d, sr):
    """(median F0, F0 IQR, median spectral centroid) over voiced frames."""
    win, hop = int(0.04*sr), int(0.02*sr)
    f0s, cents = [], []
    for i in range(0, len(d)-win, hop):
        x = d[i:i+win]
        if np.sqrt((x**2).mean()) < 200: continue
        x = x - x.mean()
        ac = np.correlate(x, x, 'full')[win-1:]
        lo, hi = int(sr/350), int(sr/60)
        if hi >= len(ac): continue
        seg = ac[lo:hi]
        if seg.max() <= 0: continue
        lag = lo + int(np.argmax(seg))
        if ac[lag] > 0.3*ac[0]: f0s.append(sr/lag)
        X = np.abs(np.fft.rfft(x*np.hanning(win)))
        fr = np.fft.rfftfreq(win, 1/sr)
        cents.append((X*fr).sum()/X.sum())
    f0s = np.array(f0s)
    return (np.median(f0s), np.percentile(f0s, 75)-np.percentile(f0s, 25),
            np.median(cents))

# Reference = the consensus of segments 1-5 (already final).
refs = np.array([profile(*load(f"audio/seg{i}.wav")) for i in range(1, 6)])
ref = np.median(refs, axis=0)
print(f"reference (segs 1-5): F0={ref[0]:.1f}Hz IQR={ref[1]:.1f} centroid={ref[2]:.0f}Hz\n")

md = open("script.md", encoding="utf-8").read()
segs = {k: re.sub(r"\s+", " ", v).strip() for k, v in dict(re.findall(
    r"\*\*Narration \(seg(\d)\.txt\):\*\*\n(.*?)(?=\n## |\Z)", md, re.S)).items()}

def score(p):
    """Weighted distance from the reference profile; lower is a better match."""
    f0, iqr, c = p
    return (abs(f0-ref[0])/ref[0])*2.0 + (abs(iqr-ref[1])/ref[1])*1.0 + (abs(c-ref[2])/ref[2])*0.5

best = None
for attempt in range(1, 4):
    try:
        pcm = T.patient_synth(segs["0"], f"seg0-cand{attempt}", deadline_s=900)
    except SystemExit as e:
        print(f"candidate {attempt}: {e} -- stopping", flush=True); break
    tmp = f"audio/_cand0_{attempt}.wav"
    T.wav_from_pcm(pcm, tmp)
    d, sr = load(tmp)
    p = profile(d, sr)
    s = score(p)
    print(f"candidate {attempt}: dur={len(d)/sr:5.1f}s F0={p[0]:6.1f} IQR={p[1]:5.1f} "
          f"centroid={p[2]:5.0f}  score={s:.4f}", flush=True)
    if best is None or s < best[0]:
        best = (s, tmp, len(d)/sr, p)

if best:
    s, tmp, dur, p = best
    os.replace(tmp, "audio/seg0.wav")
    import json
    dp = "audio/durations.json"
    durs = json.load(open(dp)); durs["0"] = dur
    json.dump(durs, open(dp, "w"), indent=1)
    print(f"\nKEPT {tmp} (score {s:.4f}) -> audio/seg0.wav  dur={dur:.1f}s")
    print(f"final seg0 profile: F0={p[0]:.1f} IQR={p[1]:.1f} centroid={p[2]:.0f}")
for i in range(1, 4):
    f = f"audio/_cand0_{i}.wav"
    if os.path.exists(f) and os.path.getsize("audio/seg0.wav") != os.path.getsize(f):
        os.remove(f)
