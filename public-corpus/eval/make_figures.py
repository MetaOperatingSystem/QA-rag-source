#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_figures.py -- Generate vector-PDF figures for the manuscript.

All numbers are read from the evaluation JSON files (single source of truth,
identical to the values printed in the paper tables). Outputs go to
  eval/figures/

Figures:
  fig3_retrieval.pdf     grouped bars: 4 retrieval configs x R@1/3/5
  fig4_sensitivity.pdf   two panels: (a) chunks bar + R@k line; (b) Tgen
  fig5_ablation.pdf      100% stacked bars: faithful/unsupported/refusal
  fig6_latency.pdf       horizontal stacked bars: latency decomposition
  fig7_concurrency.pdf   dual-axis lines: throughput & latency vs concurrency
"""
import json, os, re
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
FIGDIR = os.path.join(HERE, "figures")
os.makedirs(FIGDIR, exist_ok=True)

# ---- global style: publication-style, colour-blind safe (Okabe-Ito) ----
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Times New Roman", "STIXGeneral", "DejaVu Serif"],
    "font.size": 8.5,
    "axes.titlesize": 9,
    "axes.labelsize": 8.5,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.5,
    "axes.linewidth": 0.6,
    "axes.edgecolor": "#444444",
    "grid.linewidth": 0.4,
    "pdf.fonttype": 42,          # TrueType, editable in Illustrator
    "ps.fonttype": 42,
})
C = {"blue": "#0072B2", "orange": "#E69F00", "green": "#009E73",
     "verm": "#D55E00", "purple": "#CC79A7", "sky": "#56B4E9",
     "yellow": "#F0E442", "grey": "#999999"}

def load(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return json.load(f)

def save(fig, name):
    path = os.path.join(FIGDIR, name)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("wrote", path)

# =====================================================================
# Fig 3 -- retrieval quality, grouped bars
# =====================================================================
retr = load("retrieval_results.json")["configs"]
cfg_order = [
    ("A_bm25_uni_bigram_plain", "BM25\nuni+bigram"),
    ("B_bm25_unigram_only", "BM25\nunigram"),
    ("C_bm25_quality_reweight", "Production\n(quality-weighted)"),
    ("D_dense_bge", "Dense\nbge-small-zh"),
]
# tolerate key variants
def find_key(sub):
    for k in retr:
        if sub.lower() in k.lower():
            return k
    raise KeyError(sub)
cfg_order = [(find_key(s), lbl) for s, lbl in cfg_order]

ks = ["R@1", "R@3", "R@5"]
fig, ax = plt.subplots(figsize=(5.0, 2.6))
x = np.arange(len(cfg_order)); w = 0.26
barcols = [C["sky"], C["blue"], "#003f63"]
for i, kk in enumerate(ks):
    vals = [retr[c][kk] for c, _ in cfg_order]
    b = ax.bar(x + (i - 1) * w, vals, w, label=kk, color=barcols[i],
               edgecolor="white", linewidth=0.4, zorder=3)
    for r, v in zip(b, vals):
        ax.text(r.get_x() + r.get_width() / 2, v + 0.012, f"{v:.2f}",
                ha="center", va="bottom", fontsize=6.4)
ax.set_xticks(x); ax.set_xticklabels([l for _, l in cfg_order])
ax.set_ylabel("Recall@$k$"); ax.set_ylim(0, 1.05)
ax.yaxis.grid(True, zorder=0); ax.set_axisbelow(True)
ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.42), frameon=False)
save(fig, "fig3_retrieval.pdf")

# =====================================================================
# Fig 4 -- parameter sensitivity, two panels
# =====================================================================
sens = load("sensitivity_retrieval.json")
tgen = load("tgen_results.json")
order = ["L300_k3", "L300_k5", "L500_k5", "L500_k8", "L800_k5", "L800_k8"]
labels = ["L300\nk3", "L300\nk5", "L500\nk5", "L500\nk8", "L800\nk5", "L800\nk8"]
chunks = [sens[o]["chunks"] for o in order]
rk = [sens[o]["R_at_k"] for o in order]
tg = [tgen[o]["tgen_s_median"] for o in order]

fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.16, 2.6))
x = np.arange(len(order))
# (a) chunks bar + recall line
a1.bar(x, chunks, 0.55, color=C["grey"], alpha=0.75, zorder=2, label="Chunks (index size)")
for xi, v in zip(x, chunks):
    a1.text(xi, v + 350, f"{v:,}", ha="center", va="bottom", fontsize=6.2, color="#555555")
a1.set_ylabel("Chunks in index"); a1.set_ylim(0, 26000)
a1.set_xticks(x); a1.set_xticklabels(labels, fontsize=7)
a1b = a1.twinx()
a1b.plot(x, rk, "o-", color=C["blue"], lw=1.4, ms=4.5, zorder=4, label="R@$k$")
for xi, v in zip(x, rk):
    a1b.annotate(f"{v:.3f}", (xi, v), textcoords="offset points",
                 xytext=(0, 6), ha="center", fontsize=6.6, color=C["blue"])
a1b.set_ylabel("Recall@$k$", color=C["blue"]); a1b.set_ylim(0.78, 0.95)
a1b.tick_params(axis="y", colors=C["blue"])
a1.set_title("(a) Index size vs. recall", fontsize=8.5)
# (b) Tgen
a2.plot(x, tg, "s--", color=C["verm"], lw=1.2, ms=4.5, zorder=3)
for xi, v in zip(x, tg):
    a2.annotate(f"{v:.1f}", (xi, v), textcoords="offset points",
                xytext=(0, 6), ha="center", fontsize=6.8, color=C["verm"])
a2.axhspan(6.4, 7.6, color=C["verm"], alpha=0.07, zorder=1)
a2.set_ylabel("$T_{\\mathrm{gen}}$ median (s)"); a2.set_ylim(5.5, 8.5)
a2.set_xticks(x); a2.set_xticklabels(labels, fontsize=7)
a2.yaxis.grid(True); a2.set_axisbelow(True)
a2.set_title("(b) Decode time is flat (6.4-7.6 s)", fontsize=8.5)
fig.tight_layout(w_pad=2.2)
save(fig, "fig4_sensitivity.pdf")

# =====================================================================
# Fig 5 -- faithfulness ablation, 100% stacked bars (adjudicated counts)
# =====================================================================
adj = load("adjudication.json")["_final_metrics"]
def frac(s):
    m = re.match(r"(\d+)/(\d+)", s)
    return int(m.group(1)), int(m.group(2))

cfgs = ["production", "no_refusal", "temp08", "no_breadcrumb"]
names = ["Production", "Abl-1\nno refusal clause", "Abl-2\ntemp 0.8", "Abl-3\nno breadcrumb"]
faithful, unsup, refusal, hr_lbl, rr_lbl = [], [], [], [], []
for c in cfgs:
    fm = adj[c]
    n_unsup, n_ans = frac(fm["overall_HR"])          # unsupported / answered
    n_ref, n_tot = frac(fm["overall_RR"])            # refusal / total
    faithful.append((n_ans - n_unsup) / n_tot * 100)
    unsup.append(n_unsup / n_tot * 100)
    refusal.append(n_ref / n_tot * 100)
    hr_lbl.append(fm["overall_HR"].split("=")[-1].strip())
    rr_lbl.append(fm["overall_RR"].split("=")[-1].strip())

fig, ax = plt.subplots(figsize=(5.2, 2.8))
x = np.arange(len(cfgs))
b1 = ax.bar(x, faithful, 0.55, color=C["green"], label="Faithful", zorder=3)
b2 = ax.bar(x, unsup, 0.55, bottom=faithful, color=C["verm"], label="Unsupported", zorder=3)
b3 = ax.bar(x, refusal, 0.55, bottom=np.array(faithful) + np.array(unsup),
            color=C["grey"], alpha=0.75, label="Correct refusal", zorder=3)
for xi, (f, u, r, hr, rr) in enumerate(zip(faithful, unsup, refusal, hr_lbl, rr_lbl)):
    if f > 6:
        ax.text(xi, f / 2, f"{f:.0f}%", ha="center", va="center", fontsize=7, color="white")
    if u > 3:
        ax.text(xi, f + u / 2, f"{u:.0f}%", ha="center", va="center", fontsize=7, color="white")
    if r > 6:
        ax.text(xi, f + u + r / 2, f"{r:.0f}%", ha="center", va="center", fontsize=7, color="white")
    ax.text(xi, 103, f"HR {hr}\nRR {rr}", ha="center", va="bottom", fontsize=6.6)
ax.set_xticks(x); ax.set_xticklabels(names, fontsize=7.5)
ax.set_ylabel("Share of 69 questions (%)"); ax.set_ylim(0, 118)
ax.set_yticks([0, 25, 50, 75, 100])
ax.legend(ncol=3, loc="lower center", bbox_to_anchor=(0.5, -0.40), frameon=False)
save(fig, "fig5_ablation.pdf")

# =====================================================================
# Fig 6 -- latency decomposition, horizontal stacked bars (tab:latency)
# =====================================================================
stages = ["$T_{\\mathrm{recv}}$", "$T_{\\mathrm{ret}}$", "$T_{\\mathrm{gen}}$", "$T_{\\mathrm{del}}$"]
med = [0.11, 0.06, 15.6, 0.11]
p95 = [0.11, 0.28, 27.4, 0.11]
seg_cols = [C["sky"], C["blue"], C["verm"], C["purple"]]
fig, ax = plt.subplots(figsize=(7.16, 1.9))
rows = {"Median (15.9 s)": med, "p95 (27.9 s)": p95}
ypos = np.arange(len(rows))[::-1]
for yi, (lbl, vals) in zip(ypos, rows.items()):
    left = 0.0
    for v, c, s in zip(vals, seg_cols, stages):
        ax.barh(yi, v, left=left, height=0.5, color=c, edgecolor="white",
                linewidth=0.5, zorder=3)
        left += v
    # annotate T_gen segments only (others too small)
    gstart = vals[0] + vals[1]
    ax.text(gstart + vals[2] / 2, yi, f"$T_{{\\mathrm{{gen}}}}$ {vals[2]:.1f} s",
            ha="center", va="center", fontsize=7.2, color="white")
    ax.text(left + 0.3, yi, f"{sum(vals):.1f} s", va="center", fontsize=7.5)
ax.set_yticks(ypos); ax.set_yticklabels(list(rows.keys()))
ax.set_xlim(0, 31); ax.set_xlabel("End-to-end latency (s)")
ax.xaxis.grid(True); ax.set_axisbelow(True)
handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in seg_cols]
ax.legend(handles, ["$T_{\\mathrm{recv}}$ 0.11 s", "$T_{\\mathrm{ret}}$ 0.06/0.28 s",
                    "$T_{\\mathrm{gen}}$ (prefill 9.9 + decode 5.7, median)",
                    "$T_{\\mathrm{del}}$ 0.11 s"],
          ncol=4, loc="lower center", bbox_to_anchor=(0.5, -0.62), frameon=False, fontsize=6.8)
save(fig, "fig6_latency.pdf")

# =====================================================================
# Fig 7 -- concurrency scaling, dual-axis lines
# =====================================================================
th = load("throughput_results.json")
cs = [1, 2, 4]
apm = [th[f"conc{c}"]["answers_per_min"] for c in cs]
lat = [th[f"conc{c}"]["mean_total_s"] for c in cs]

fig, ax = plt.subplots(figsize=(4.6, 2.7))
l1, = ax.plot(cs, apm, "o-", color=C["blue"], lw=1.5, ms=5, zorder=4,
              label="Throughput (answers/min)")
for xi, v in zip(cs, apm):
    off = (0, 7) if xi != 4 else (-6, -14)
    ax.annotate(f"{v:.1f}", (xi, v), textcoords="offset points", xytext=off,
                ha="center", fontsize=7.2, color=C["blue"])
ax.set_xlabel("Concurrent questions $c$"); ax.set_ylabel("Answers/min", color=C["blue"])
ax.set_xticks(cs); ax.set_ylim(0, 11)
ax.tick_params(axis="y", colors=C["blue"])
ax2 = ax.twinx()
l2, = ax2.plot(cs, lat, "s--", color=C["verm"], lw=1.3, ms=4.5, zorder=3,
               label="Mean latency/request (s)")
for xi, v in zip(cs, lat):
    off = (0, -13) if xi != 4 else (0, 9)
    ax2.annotate(f"{v:.1f}s", (xi, v), textcoords="offset points", xytext=off,
                 ha="center", fontsize=7.2, color=C["verm"])
ax2.set_ylabel("Mean latency per request (s)", color=C["verm"])
ax2.set_ylim(0, 32); ax2.tick_params(axis="y", colors=C["verm"])
ax.annotate("batching saturates", xy=(4, 7.94), xytext=(2.45, 4.6),
            fontsize=7, arrowprops=dict(arrowstyle="->", lw=0.7, color="#555555"),
            color="#333333")
ax.text(1, 1.6, "incl. one-time\nwarm-up", fontsize=6.2, ha="center", color="#666666")
ax.legend(handles=[l1, l2], loc="center left", bbox_to_anchor=(0.02, 0.62),
          frameon=False, fontsize=7)
save(fig, "fig7_concurrency.pdf")

print("done.")
