"""
Generates thumbnail for the Harmonic Orbit Space blog post.

Shows the orbit trail for Fur Elise plotted on the circle of fifths,
colored blue->red by time. Dark background, same style as the other
blog post thumbnails.

Usage:
    python src/content/blog/harmonic-orbit-space/generate_thumbnail.py
"""

import json
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from pathlib import Path

HERE = Path(__file__).parent
DATA_PATH = HERE / "orbit-data.json"
OUT_PATH  = HERE / "thumbnail.png"

# ── Load data ─────────────────────────────────────────────────────────────────
with open(DATA_PATH) as f:
    all_songs = json.load(f)

song = next(s for s in all_songs if s["id"] == "fur-elise")
dur  = song["duration"]

# ── Compute orbit coordinates from pc arrays (circle of fifths) ──────────────
def pc_to_orbit(pc):
    """Project 12-element chroma vector onto circle of fifths."""
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
        pts.append((p["t"], ox, oy, p.get("os", 0)))

# ── Circle of fifths layout ───────────────────────────────────────────────────
NOTE_NAMES = ["C", "G", "D", "A", "E", "B", "F#", "C#", "G#", "D#", "A#", "F"]
COF_ANGLES = [(i / 12) * 2 * math.pi for i in range(12)]

# ── Figure setup ──────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6.75), facecolor="#0b0e14")
ax.set_facecolor("#0b0e14")
ax.set_aspect("equal")
ax.axis("off")

# ── Reference ring ────────────────────────────────────────────────────────────
ring_theta = np.linspace(0, 2 * math.pi, 200)
ax.plot(
    np.cos(ring_theta) * 1.0,
    np.sin(ring_theta) * 1.0,
    color="white", alpha=0.06, linewidth=1.0, zorder=1
)
ax.plot(
    np.cos(ring_theta) * 1.15,
    np.sin(ring_theta) * 1.15,
    color="white", alpha=0.04, linewidth=0.5, zorder=1
)

# ── Note labels ───────────────────────────────────────────────────────────────
LABEL_R = 1.26
for i, name in enumerate(NOTE_NAMES):
    angle = COF_ANGLES[i]
    lx = math.cos(angle) * LABEL_R
    ly = math.sin(angle) * LABEL_R
    ax.text(
        lx, ly, name,
        ha="center", va="center",
        fontsize=11, color="white", alpha=0.55,
        fontfamily="monospace",
        zorder=2
    )
    tx1 = math.cos(angle) * 1.12
    ty1 = math.sin(angle) * 1.12
    tx2 = math.cos(angle) * 1.17
    ty2 = math.sin(angle) * 1.17
    ax.plot([tx1, tx2], [ty1, ty2], color="white", alpha=0.20, linewidth=0.8, zorder=2)

# ── Orbit trail ───────────────────────────────────────────────────────────────
cmap = LinearSegmentedColormap.from_list(
    "orbit",
    [(0.0, "#1155cc"), (0.4, "#2288ff"), (0.7, "#ff8822"), (1.0, "#ff3300")]
)

max_os = max(p[3] for p in pts) if pts else 1

for t, x, y, os in pts:
    frac = t / dur
    color = cmap(frac)
    sz = 8 + min(os / max_os * 40, 30)
    alpha = 0.55 + frac * 0.35
    ax.scatter(x, y, c=[color], s=sz, alpha=alpha, zorder=3, linewidths=0)

# Highlight the last point
if pts:
    _, lx, ly, _ = pts[-1]
    ax.scatter(lx, ly, c=["#ff3300"], s=120, alpha=0.95, zorder=5, linewidths=1.5,
               edgecolors="white")

# Origin reference
ax.scatter(0, 0, c="white", s=8, alpha=0.15, zorder=2, linewidths=0)

# ── Title / annotation ────────────────────────────────────────────────────────
ax.text(
    -1.42, 1.28,
    "Harmonic Orbit Space",
    fontsize=20, color="white", alpha=0.88,
    fontfamily="monospace", fontweight="bold",
    zorder=6
)
ax.text(
    -1.42, 1.12,
    "Beethoven - Fur Elise",
    fontsize=13, color="#88aacc", alpha=0.75,
    fontfamily="monospace",
    zorder=6
)
ax.text(
    -1.42, 0.98,
    f"circle of fifths projection - {dur:.0f} seconds",
    fontsize=9.5, color="#4466aa", alpha=0.65,
    fontfamily="monospace",
    zorder=6
)

# Color bar legend
legend_x = 0.78
for i, (lbl, col) in enumerate([("start", "#1155cc"), ("end", "#ff3300")]):
    ax.scatter([legend_x + i * 0.22], [-1.28], c=[col], s=55, zorder=6,
               linewidths=0, alpha=0.85)
    ax.text(legend_x + i * 0.22 + 0.06, -1.28, lbl,
            va="center", fontsize=9, color="white", alpha=0.50,
            fontfamily="monospace", zorder=6)

# ── Axis limits ───────────────────────────────────────────────────────────────
ax.set_xlim(-1.5, 1.5)
ax.set_ylim(-1.45, 1.45)

plt.tight_layout(pad=0.3)
plt.savefig(OUT_PATH, dpi=150, bbox_inches="tight", facecolor="#0b0e14")
print(f"Thumbnail saved -> {OUT_PATH}")
