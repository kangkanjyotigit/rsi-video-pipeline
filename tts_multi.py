"""Narration TTS — one Gemini request per segment, rotating across API keys.

Free tier is 10 requests/day per project, so chunking is off and both keys are
pressed into service. Resumable: skips segments already on disk.

Usage: uv run --python 3.11 python tts_multi.py [0 1 2 ...]
"""
import base64
import json
import os
import re
import struct
import sys
import time
import urllib.error
import urllib.request

# Supply your own keys — never commit them.
#   Windows:  set GEMINI_API_KEYS=key1,key2
#   Linux:    export GEMINI_API_KEYS=key1,key2
KEYS = [k.strip() for k in os.environ.get("GEMINI_API_KEYS", "").split(",") if k.strip()]
if not KEYS:
    raise SystemExit(
        "No API keys found. Set GEMINI_API_KEYS to one or more comma-separated "
        "Google AI Studio keys, e.g. GEMINI_API_KEYS=\"key1,key2\""
    )
# Ordered preference: quota is per-model-per-project, so each entry is a fresh bucket.
# gemini-3.8-flash-tts measured closest to the approved seg0 sample (F0 105 vs 96 Hz,
# spectral centroid 1437 vs 2044 Hz); 2.5-flash-preview-tts is hard-exhausted.
MODELS = [
    "gemini-3.8-flash-tts",
    "gemini-3.1-flash-tts-preview",
    "gemini-3.8-flash-lite-tts",
]
VOICE = "Charon"
HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "audio")
os.makedirs(AUD, exist_ok=True)

STYLE = (
    "You are narrating a mathematics documentary. Speak slowly and clearly, "
    "with warmth and quiet confidence. Pause briefly between sentences. "
    "Emphasise the important words lightly. Never sound rushed or like an "
    "advertisement.\n\n"
)


def wav_from_pcm(pcm, path, rate=24000):
    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + len(pcm)) + b"WAVEfmt "
                + struct.pack("<IHHIIHH", 16, 1, 1, rate, rate * 2, 2, 16)
                + b"data" + struct.pack("<I", len(pcm)) + pcm)


def synth_once(text, key, model):
    body = json.dumps({
        "contents": [{"parts": [{"text": STYLE + text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {
                "prebuiltVoiceConfig": {"voiceName": VOICE}}}}},
    ).encode()
    req = urllib.request.Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}"
        f":generateContent?key={key}",
        data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        resp = json.load(r)
    return base64.b64decode(
        resp["candidates"][0]["content"]["parts"][0]["inlineData"]["data"])


def patient_synth(text, label, deadline_s=6 * 3600):
    """Try every (model, key) pair; wait out rate limits until the deadline."""
    deadline = time.time() + deadline_s
    backoff = 30
    while time.time() < deadline:
        for model in MODELS:
            for ki, key in enumerate(KEYS, 1):
                try:
                    return synth_once(text, key, model)
                except urllib.error.HTTPError as e:
                    if e.code in (429, 500, 502, 503, 504):
                        print(f"  {label}: {model} key{ki} HTTP {e.code}",
                              flush=True)
                        continue
                    raise
        print(f"  {label}: all model/key pairs limited, sleep {backoff}s",
              flush=True)
        time.sleep(backoff)
        backoff = min(int(backoff * 1.5), 600)
    raise SystemExit(f"{label}: deadline reached")


def main():
    md = open(os.path.join(HERE, "script.md"), encoding="utf-8").read()
    segs = {k: re.sub(r"\s+", " ", v).strip() for k, v in dict(re.findall(
        r"\*\*Narration \(seg(\d)\.txt\):\*\*\n(.*?)(?=\n## |\Z)", md, re.S)).items()}
    order = sys.argv[1:] or sorted(segs)
    dpath = os.path.join(AUD, "durations.json")
    durs = json.load(open(dpath)) if os.path.exists(dpath) else {}

    for i in order:
        out = os.path.join(AUD, f"seg{i}.wav")
        if os.path.exists(out) and os.path.getsize(out) > 200_000:
            d = (os.path.getsize(out) - 44) / 48000.0
            durs[i] = d
            print(f"seg{i}: present ({d:.1f}s), skip", flush=True)
            continue
        text = segs[i]
        print(f"seg{i}: {len(text.split())} words", flush=True)
        pcm = patient_synth(text, f"seg{i}")
        wav_from_pcm(pcm, out)
        d = len(pcm) / 48000.0
        durs[i] = d
        json.dump(durs, open(dpath, "w"), indent=1)
        print(f"seg{i}: {d:.1f}s OK", flush=True)

    print("durations:", {k: round(float(v), 1) for k, v in sorted(durs.items())},
          flush=True)
    print("TOTAL:", round(sum(float(v) for v in durs.values()), 1), "s", flush=True)


if __name__ == "__main__":
    main()
