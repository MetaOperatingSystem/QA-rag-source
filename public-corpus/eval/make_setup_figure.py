#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_setup_figure.py -- Compose the physical deployment figure (Fig:setup).

Full chain:  Jetson AGX Xavier (inference) <-- campus LAN --> MacBook M3
(service/retrieval/bot) -- outbound WebSocket --> Feishu cloud --> group members.

Photos (background-matted RGBA PNGs) are embedded as rasters; all text,
arrows and icons are vector. Output: figures/fig0_setup.pdf
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from matplotlib.patches import FancyArrowPatch, Ellipse, FancyBboxPatch, Circle

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(FIGDIR, exist_ok=True)

plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
    "pdf.fonttype": 42,
})
C = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73",
     "verm": "#D55E00", "purple": "#CC79A7", "sky": "#56B4E9",
     "grey": "#666666"}

W, H = 7.16, 3.35
fig = plt.figure(figsize=(W, H))
fig.patch.set_facecolor("white")


def _trimmed(path, pad=6):
    """Crop transparent borders of a matted RGBA PNG to its alpha bbox."""
    from PIL import Image
    im = Image.open(path).convert("RGBA")
    bbox = im.getchannel("A").getbbox()
    if bbox:
        l, t, r, b = bbox
        l = max(0, l - pad); t = max(0, t - pad)
        r = min(im.width, r + pad); b = min(im.height, b + pad)
        im = im.crop((l, t, r, b))
    return im


def photo(path, x, y, w, h):
    ax = fig.add_axes([x, y, w, h])
    ax.imshow(_trimmed(path))
    ax.set_aspect("equal")
    ax.axis("off")
    return ax


def label(x, y, title, lines, color, ha="center", title_fs=8.2, body_fs=7.0):
    fig.text(x, y, title, ha=ha, va="top", fontsize=title_fs,
             fontweight="bold", color=color)
    fig.text(x, y - 0.052, "\n".join(lines), ha=ha, va="top",
             fontsize=body_fs, color="#333333", linespacing=1.35)


# ---------------- photos ----------------
photo(os.path.join(FIGDIR, "assets", "xavier.png"), 0.005, 0.30, 0.235, 0.66)
photo(os.path.join(FIGDIR, "assets", "macbook.png"), 0.435, 0.30, 0.235, 0.66)

label(0.1225, 0.27, "Inference node",
      ["Jetson AGX Xavier",
       "Ollama (Docker)",
       "qwen2.5:7b-instruct-q4_K_M",
       "192.168.1.75"], C["blue"])

label(0.5525, 0.27, "Service / retrieval node",
      ["MacBook (Apple M3)",
       "ingest \u00b7 index \u00b7 BM25 (14,076 chunks)",
       "Feishu bot client (lark-oapi)",
       "192.168.1.85"], C["green"])

# ---------------- LAN arrow (Xavier <-> MacBook) ----------------
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 1); ax.set_ylim(0, 1)
ax.axis("off")
ar = FancyArrowPatch((0.252, 0.58), (0.425, 0.58), arrowstyle="<|-|>",
                     mutation_scale=13, lw=1.6, color=C["grey"])
ax.add_patch(ar)
fig.text(0.3385, 0.80, "Campus LAN (same subnet)", ha="center", fontsize=7.6,
         fontweight="bold", color="#333333")
fig.text(0.3385, 0.735, "HTTP :11434\nOpenAI-compatible endpoint", ha="center",
         va="top", fontsize=6.8, color="#333333", linespacing=1.3)
fig.text(0.3385, 0.50, "$T_{gen} \\approx 15.6$ s", ha="center", fontsize=6.8,
         color=C["verm"])

# ---------------- wss arrow (MacBook -> cloud) ----------------
ar2 = FancyArrowPatch((0.685, 0.66), (0.795, 0.66), arrowstyle="-|>",
                      mutation_scale=13, lw=1.6, color=C["purple"])
ax.add_patch(ar2)
fig.text(0.74, 0.775, "WebSocket long\nconnection\n(outbound only)",
         ha="center", va="top", fontsize=6.6, color="#333333", linespacing=1.25)
fig.text(0.74, 0.575, "$T_{del} \\approx 0.11$ s", ha="center", fontsize=6.8,
         color=C["verm"])

# ---------------- Feishu cloud icon ----------------
cx, cy = 0.895, 0.70
for dx, dy, rw, rh in [(-0.030, -0.010, 0.030, 0.030),
                       (0.000, 0.015, 0.038, 0.038),
                       (0.034, -0.008, 0.028, 0.028)]:
    ax.add_patch(Ellipse((cx + dx, cy + dy), rw * 2, rh * 2,
                         color=C["sky"], ec="none", zorder=2))
ax.add_patch(FancyBboxPatch((cx - 0.055, cy - 0.045), 0.115, 0.045,
                            boxstyle="round,pad=0.004", color=C["sky"],
                            ec="none", zorder=2))
fig.text(cx, cy - 0.005, "Feishu\ncloud", ha="center", va="center",
         fontsize=6.8, fontweight="bold", color="white", zorder=3,
         linespacing=1.1)

# ---------------- group members (phone + laptop icons) ----------------
my = 0.33
# phone
ax.add_patch(FancyBboxPatch((0.845, my - 0.055), 0.045, 0.11,
                            boxstyle="round,pad=0.004", fc="white",
                            ec=C["grey"], lw=1.1))
ax.add_patch(Circle((0.8675, my - 0.038), 0.005, fc=C["grey"], ec="none"))
# laptop
ax.add_patch(FancyBboxPatch((0.922, my - 0.030), 0.055, 0.075,
                            boxstyle="round,pad=0.003", fc="white",
                            ec=C["grey"], lw=1.1))
ax.plot([0.915, 0.984], [my - 0.045, my - 0.045], color=C["grey"], lw=1.4)
fig.text(0.916, 0.20, "group members\n@bot in chat", ha="center", va="top",
         fontsize=6.6, color="#333333", linespacing=1.25)

# arrow cloud -> members
ar3 = FancyArrowPatch((0.895, 0.615), (0.905, 0.415), arrowstyle="-|>",
                      mutation_scale=11, lw=1.4, color=C["purple"],
                      linestyle=(0, (4, 2)))
ax.add_patch(ar3)

# service-side retrieval tag
fig.text(0.5525, 0.955, "$T_{ret}$ = 58 ms (BM25, median)", ha="center",
         fontsize=6.8, color=C["verm"])
fig.text(0.1225, 0.955, "8.2 GB model, fully on GPU", ha="center",
         fontsize=6.8, color=C["grey"])

out = os.path.join(FIGDIR, "fig0_setup.pdf")
fig.savefig(out, bbox_inches="tight", pad_inches=0.02)
print("wrote", out)
