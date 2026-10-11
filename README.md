# Automated explainer-video pipeline

Turns a written script into a finished 10-minute 1080p explainer video, unattended —
3Blue1Brown style, from narration text to a muxed file.

The pipeline was built and debugged end-to-end on one real production:
`script.md` (a ~10 min video on regularised recursive self-improvement).

## Pipeline stages

```
script.md
   |  mathgen.py ......... generate Manim math scenes from the script
   |  flatten_svg.py ..... flatten SVG output for compositing
   |  tts_multi.py ....... Gemini TTS narration, one request per segment,
   |                      rotating across API keys, resumable
   |  voicecmp.py ........ compare candidate voices by F0 / spectral centroid
   |  calibrate.py ....... per-segment audio level calibration
   |  deadair.py ......... detect and trim dead air
   |  subs.py ............ build and time subtitles against the narration
   |  seg0_match.py ...... align segment boundaries to the audio
   |  animtime.py ........ reconcile animation timing to narration length
   |  edgeaudit.py / edgecrop.py / edgewhat.py ... frame-edge QA passes
   |  final_mux.sh ....... FFmpeg mux into the final 1080p file
   v
out/final.mp4
```

## Design notes

- **Resumable by construction** — every stage skips work already on disk, so a
  failed TTS request doesn't cost you the whole run.
- **Key rotation** — free-tier TTS quota is per-project, so requests rotate across
  keys and model variants; the model preference order was chosen by measuring
  output against an approved reference sample (F0 and spectral centroid), not by
  guessing.
- **QA stages are separate scripts** — audio edge, crop and dead-air problems were
  each isolated into their own tool so they could be re-run independently.

## Setup

```bash
pip install -r requirements.txt
```

Set your keys as environment variables — never commit them:

```bash
# Windows
set GEMINI_API_KEYS=key1,key2
# Linux / macOS
export GEMINI_API_KEYS=key1,key2
```

## Notes

- `mathsvg/` contains generated scene output as a sample.
- Rendered media (`audio/`, `out/`, `scenes/`, `assets/`) is excluded — it is
  large and reproducible from the scripts.
- `script.md` is included as the worked example.
