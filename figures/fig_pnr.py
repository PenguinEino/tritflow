"""Fig. 7 — placement and two-metal routing of the 4-trit adder (64 cells)."""

import re

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.lines import Line2D
from matplotlib.patches import Patch, Rectangle

import data
import paperstyle as style

DIGIT = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]  # categorical slots 1-4, fixed order
DIGIT_FILL = ["#cde2fb", "#fbd5c4", "#c4ecdd", "#fbe6b3"]


def digit(hier):
    m = re.search(r"\[(\d+)\]", hier or "")
    return int(m.group(1)) if m else None


def cells(ax, placements, die, fill=True):
    patches, faces, edges = [], [], []
    for p in placements:
        k = digit(p.get("hier") or p["inst"])
        patches.append(Rectangle((p["x"], p["y"]), p["width"], p["height"]))
        faces.append(DIGIT_FILL[k] if (fill and k is not None) else "#f1efe8")
        edges.append(DIGIT[k] if k is not None else style.MUTED)
    ax.add_collection(PatchCollection(patches, facecolors=faces, edgecolors=edges, linewidths=0.6,
                                      zorder=2))
    ax.add_patch(Rectangle((0, 0), die[0], die[1], fill=False, ec=style.INK2, lw=0.6, zorder=1))
    ax.set_xlim(-20, die[0] + 20)
    ax.set_ylim(-20, die[1] + 20)
    ax.set_aspect("equal")
    ax.grid(False)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def routes(ax, wires):
    for layer, color, z in (("M1", "#2a78d6", 4), ("M2", "#6250d6", 5)):
        segs = []
        for w in wires:
            if w["layer"] != layer:
                continue
            pts = w["points"]
            segs += [(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        ax.add_collection(LineCollection(segs, colors=color, linewidths=0.45, alpha=0.85, zorder=z))


def make():
    style.use()
    d = data.load("build/adder4/adder4.pnr.json") if False else __import__("json").loads(
        (data.ROOT / "build/adder4/adder4.pnr.json").read_text())
    die = d["die"]
    hist = d["history"]
    fig = plt.figure(figsize=(style.DOUBLE, 2.75))
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.95], wspace=0.12)
    a0 = fig.add_subplot(gs[0])
    a1 = fig.add_subplot(gs[1])
    a2 = fig.add_subplot(gs[2])

    cells(a0, hist[0]["placements"], die)
    a0.set_title("      initial placement (signal order)", loc="left")
    cells(a1, d["placements"], die, fill=True)
    routes(a1, d["wires"])
    a1.set_title(f"      annealed and routed, {die[0]:.0f} × {die[1]:.0f} µm", loc="left")

    steps = [h["step"] for h in hist]
    hp = [h["hpwl"] / 1e3 for h in hist]
    a2.plot(steps, hp, color=style.INK, lw=1.1)
    a2.plot(steps[0], hp[0], "o", ms=3.5, color=style.INK)
    a2.plot(steps[-1], hp[-1], "o", ms=3.5, color=style.INK)
    a2.annotate(f"{hp[0]:.0f} mm", (steps[0], hp[0]), xytext=(6, 0), textcoords="offset points",
                va="center", fontsize=7)
    a2.annotate(f"{hp[-1]:.0f} mm ({(1 - hp[-1] / hp[0]) * 100:.0f} % shorter)", (steps[-1], hp[-1]),
                xytext=(-2, -16), textcoords="offset points", ha="right", fontsize=7)
    a2.set_xlabel("Annealing step")
    a2.set_ylabel("Half-perimeter wirelength (mm)")
    a2.set_ylim(0, hp[0] * 1.12)
    pos = a2.get_position()
    a2.set_position([pos.x0 + 0.06, pos.y0 + 0.08, pos.width - 0.06, pos.height - 0.12])

    keys = [Patch(facecolor=DIGIT_FILL[i], edgecolor=DIGIT[i], lw=0.6, label=f"trit {i} full adder")
            for i in range(4)]
    keys += [Line2D([], [], color="#2a78d6", lw=1, label="Metal 1 (horizontal, channels)"),
             Line2D([], [], color="#6250d6", lw=1, label="Metal 2 (vertical, over cells)")]
    fig.legend(handles=keys, loc="lower center", ncol=6, bbox_to_anchor=(0.5, -0.04),
               handlelength=1.3, columnspacing=1.0, fontsize=6.5)
    style.panel(a0, "a", x=0.0, y=1.0)
    style.panel(a1, "b", x=0.0, y=1.0)
    style.panel(a2, "c", x=-0.3, y=1.0)
    return style.save(fig, "fig_pnr")


if __name__ == "__main__":
    print(make())
