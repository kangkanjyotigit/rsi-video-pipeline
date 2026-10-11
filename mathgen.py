"""Typeset math to clean single-path SVGs using matplotlib's TextPath.

matplotlib's SVG export emits <use xlink:href="#glyph">, which Manim's parser
ignores (all glyphs land on top of each other). TextPath + to_polygons() gives
real filled outlines that we write as one flat polygon path.
"""
import os
import matplotlib
matplotlib.use("Agg")
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mathsvg")
os.makedirs(OUT, exist_ok=True)
matplotlib.rcParams["mathtext.fontset"] = "stix"

EXPRS = {
    "H_next": r"$H_{n+1} = F(H_n)$",
    "F_def": r"$F: \mathrm{propose} \rightarrow \mathrm{test} \rightarrow \mathrm{keep}$",
    "keep": r"$H_{n+1} = \arg\max_{H} \; \hat{s}(H) - \lambda C(H)$",
    "contract": r"$\|F(H) - F(H^\prime)\| \leq \kappa \|H - H^\prime\|, \quad \kappa < 1$",
    "fixed": r"$H^\star = F(H^\star)$",
    "goodhart": r"$\hat{s}(H) \uparrow \quad \mathrm{while} \quad s(H) \downarrow$",
    "compound": r"$H_n = (1-\epsilon)^n H_0 + \epsilon \sum_k (1-\epsilon)^k u_k$",
    "trust": r"$\theta_{n+1} = \theta_n - \eta \nabla J(\theta_n)$",
    "lam": r"$J_\lambda(\theta) = J(\theta) + \lambda C(\theta)$",
    "deriv": r"$|F^\prime(x^\star)| < 1 \Rightarrow \mathrm{stable\ fixed\ point}$",
    "gate": r"$\mathrm{accept} \Leftrightarrow \hat{s}(H^\prime) > \hat{s}(H_\mathrm{best})$",
    "cobweb": r"$x_{n+1} = F(x_n)$",
    "score": r"$\hat{s}$",
    "s": r"$s$",
    "theta": r"$\theta$",
    "delta": r"$\delta$",
    "lambda": r"$\lambda$",
    "kappa": r"$\kappa$",
    "eta": r"$\eta$",
}

SCALE = 100.0


def render(name: str, expr: str) -> str:
    tp = TextPath((0, 0), expr, size=1, prop=FontProperties(size=1))
    polys = [p for p in tp.to_polygons() if len(p) >= 3]
    if not polys:
        raise ValueError(f"no outlines for {name}")

    allpts = [p for pol in polys for p in pol]
    x0 = min(p[0] for p in allpts)
    x1 = max(p[0] for p in allpts)
    y0 = min(p[1] for p in allpts)
    y1 = max(p[1] for p in allpts)
    h = (y1 - y0) * SCALE

    parts = []
    for pol in polys:
        for i, (x, y) in enumerate(pol):
            X = (x - x0) * SCALE
            Y = (y1 - y) * SCALE          # flip into SVG's downward-y space
            parts.append(("M" if i == 0 else "L") + f" {X:.2f} {Y:.2f}")
        parts.append("Z")
    w = (x1 - x0) * SCALE

    svg = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.2f}" '
        f'height="{h:.2f}" viewBox="0 0 {w:.2f} {h:.2f}">\n'
        f'  <path d="{" ".join(parts)}" fill="#000000" stroke="none"/>\n'
        "</svg>\n"
    )
    p = os.path.join(OUT, name + ".svg")
    with open(p, "w", encoding="utf-8") as f:
        f.write(svg)
    return p


if __name__ == "__main__":
    for k, v in EXPRS.items():
        p = render(k, v)
        print(k, os.path.getsize(p), "bytes")
