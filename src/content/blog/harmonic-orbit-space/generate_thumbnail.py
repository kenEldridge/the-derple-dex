"""
Generates thumbnail matching the viewer's static cloud preview.

Dark #0d1117 background, all orbit points shown faintly with
blue->purple time coloring — exactly what you see before pressing Play.

Usage:
    python src/content/blog/harmonic-orbit-space/generate_thumbnail.py
"""

import json
import math
import colorsys
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

HERE = Path(__file__).parent
DATA_PATH = HERE / "orbit-data.json"
OUT_PATH  = HERE / "thumbnail.png"

BG = "#0d1117"

with open(DATA_PATH) as f:
    all_songs = json.load(f)

song = next(s for s in all_songs if s["id"] == "fur-elise")
dur = song["duration"]


def pc_to_orbit(pc):
    x, y, w = 0.0, 0.0, 0.0
    for i in range(12):
        v = pc[i] if pc[i] else 0
        angle = (2 * math.pi * ((i * 7) % 12)) / 12
        x += math.cos(angle) * v
        y += math.sin(angle) * v
        w += v
    if w < 1e-9:
        return None, None
    return x / w, y / w


pts = []
for p in song["points"]:
    ox, oy = pc_to_orbit(p["pc"])
    if ox is not None:
        pts.append((p["t"], ox, oy))

xs = [p[1] for p in pts]
ys = [p[2] for p in pts]

# ── Figure: match viewer proportions (wider than tall) ────────────────────────
fig, ax = plt.subplots(figsize=(12, 6.75), facecolor=BG)
ax.set_facecolor(BG)
ax.set_aspect("equal")
ax.axis("off")

# ── Static cloud matching the viewer's showStaticCloud() ──────────────────────
# Viewer JS: hsla((1-tn)*240, 60%, 45%, 1) at opacity 0.35, size 5
# CSS hue: 240=blue, 0=red. colorsys uses 0-1 range where 0=red, 0.667=blue
for t, x, y in pts:
    tn = t / dur if dur > 0 else 0
    css_hue_deg = (1 - tn) * 240  # 240 (blue) -> 0 (red)
    # Convert CSS hue (0=red, 240=blue) to colorsys hue (0=red, 0.667=blue)
    py_hue = css_hue_deg / 360.0
    r, g, b = colorsys.hls_to_rgb(py_hue, 0.45, 0.6)
    ax.scatter(x, y, c=[(r, g, b)], s=6, alpha=0.35, linewidths=0, zorder=2)

# ── Tight padding around the cloud ───────────────────────────────────────────
xmn, xmx = min(xs), max(xs)
ymn, ymx = min(ys), max(ys)
xpad = (xmx - xmn) * 0.15
ypad = (ymx - ymn) * 0.15
ax.set_xlim(xmn - xpad, xmx + xpad)
ax.set_ylim(ymn - ypad, ymx + ypad)

plt.tight_layout(pad=0)
plt.savefig(OUT_PATH, dpi=150, bbox_inches="tight", facecolor=BG, pad_inches=0.1)
print(f"Thumbnail saved -> {OUT_PATH}")
