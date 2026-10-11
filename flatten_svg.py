"""Flatten matplotlib SVGs: inline <use xlink:href="#id"> as concrete <path>.

Manim's SVG parser ignores <use>/<defs>, which rendered math as a solid block.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SVG_DIR = ROOT / "mathsvg"

DEF_RE = re.compile(r'<path\s+id="([^"]+)"([^>]*?)/>', re.S)
USE_RE = re.compile(r'<use\s+xlink:href="#([^"]+)"\s*([^>]*?)/>', re.S)
DEFS_RE = re.compile(r"<defs>.*?</defs>", re.S)


def d_of(attrs: str) -> str:
    m = re.search(r'\sd="([^"]*)"', attrs, re.S)
    return m.group(1) if m else ""


def flatten(path: Path) -> bool:
    s = path.read_text(encoding="utf-8")
    if "<use" not in s:
        return False
    defs = {m.group(1): d_of(m.group(2)) for m in DEF_RE.finditer(s)}
    defs.update({m.group(1): d_of(m.group(2))
                 for m in re.finditer(r'<path\s+([^>]*?)id="([^"]+)"([^>]*?)/>', s, re.S)
                 for _ in [0]
                 if (lambda g2, g1, g3: True)(m.group(2), m.group(1), m.group(3))})

    def sub(m):
        ref, attrs = m.group(1), m.group(2)
        d = defs.get(ref)
        if not d:
            return ""
        tr = re.search(r'transform="([^"]*)"', attrs)
        t = f' transform="{tr.group(1)}"' if tr else ""
        return f'<path d="{d}"{t} fill="#000000"/>'

    out = USE_RE.sub(sub, s)
    out = DEFS_RE.sub("", out)
    path.write_text(out, encoding="utf-8")
    return True


if __name__ == "__main__":
    n = 0
    for p in sorted(SVG_DIR.glob("*.svg")):
        if flatten(p):
            n += 1
            print("flattened", p.name)
    print(n, "files")
