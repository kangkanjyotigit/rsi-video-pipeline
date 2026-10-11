"""Build seg-level SRT subtitles: sentences distributed by char count."""
import re, os

HERE = os.path.dirname(os.path.abspath(__file__))
AUD = os.path.join(HERE, "audio")

def dur(i):
    import subprocess
    o = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", os.path.join(AUD, f"seg{i}.wav")]).decode().strip()
    return float(o)

def ts(s):
    h, s = divmod(s, 3600); m, s = divmod(s, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")

md = open(os.path.join(HERE, "script.md"), encoding="utf-8").read()
blocks = dict(re.findall(r"\*\*Narration \(seg(\d)\.txt\):\*\*\n(.*?)(?=\n## |\Z)", md, re.S))
entries, n, t0 = [], 1, 0.0
for i in "012345":
    text = re.sub(r"\s+", " ", blocks[i]).strip()
    sents = [x.strip() for x in re.split(r"(?<=[.!?])\s+", text) if x.strip()]
    total_chars = sum(len(x) for x in sents)
    d = dur(i)
    t = t0
    for sn in sents:
        dd = d * len(sn) / total_chars
        entries.append(f"{n}\n{ts(t)} --> {ts(t + dd)}\n{sn}\n")
        n += 1; t += dd
    t0 += d
open(os.path.join(HERE, "out", "rsi_video.srt"), "w", encoding="utf-8").write("\n".join(entries))
print(f"{len(entries)} cues, total {t0:.1f}s")
