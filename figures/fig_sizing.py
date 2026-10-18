"""Fig. 3 — sizing trade-off: middle-level accuracy versus static current (source netlists, 27 °C)."""

import json

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from tritflow import ROOT

import style

RR_SHADE = {20.0: "#9ec5f4", 30.0: "#2a78d6", 45.0: "#104281"}


def grid(cell):
    return json.loads((ROOT / f"cells/out/sizing/{cell}.grid.json").read_text())


def rr(row):
    return row["dimensions"]["RP"]["l_um"]


def scatter(ax, cell, floor_mv=None, limit=True):
    d = grid(cell)
    rows = [r for r in d["rows"] if r["max_error_v"] is not None]
    for r in rows:
        x = r["max_static_current_a"] * 1e3
        y = r["max_error_v"] * 1e3
        c = RR_SHADE[rr(r)]
        ok = r["max_error_v"] <= 0.5
        marker = "o"
        if floor_mv and y < floor_mv:
            y, marker = floor_mv, "v"
        ax.plot(x, y, marker, ms=3.6, mfc=c if ok else "white", mec=c, mew=0.8, zorder=3,
                clip_on=False)
    for length, color in RR_SHADE.items():
        xs = [r["max_static_current_a"] * 1e3 for r in rows if rr(r) == length]
        ax.text(np.median(xs), 1.0, f"{length:.0f} µm", transform=ax.get_xaxis_transform(),
                ha="center", va="bottom", fontsize=6.5, color=color)
    a = d["rows"][d["adopted_index"]]
    ax.plot(a["max_static_current_a"] * 1e3, a["max_error_v"] * 1e3, "o", ms=8.5, mfc="none",
            mec=style.INK, mew=0.9, zorder=4)
    ax.annotate("taped-out size", (a["max_static_current_a"] * 1e3, a["max_error_v"] * 1e3),
                xytext=(10, -14), textcoords="offset points", fontsize=7, color=style.INK,
                arrowprops=dict(arrowstyle="-", lw=0.6, color=style.INK))
    if limit:
        ax.axhline(500, color=style.INK2, lw=0.7, ls=(0, (3, 2)))
        ax.text(0.02, 540, "±0.5 V limit", transform=ax.get_yaxis_transform(),
                fontsize=6.5, color=style.INK2, va="bottom", ha="left")
        ax.set_yscale("log")
    ax.set_xlabel("Max static current (mA)")
    return d


def transfers(ax):
    """INV transfer curves for the three resistor lengths at the taped-out MOS sizes."""
    d = grid("INV")
    a = d["rows"][d["adopted_index"]]["dimensions"]
    style.bands(ax)
    for r in d["rows"]:
        dm = r["dimensions"]
        if all(dm[k] == a[k] for k in ("MP", "MN")) and r["transfer"]:
            t = r["transfer"]["data"]
            ax.plot(t["v-sweep"], t["v(y)"], color=RR_SHADE[rr(r)], lw=1.1,
                    label=f"$L_R$ = {rr(r):.0f} µm")
    ax.set_xlabel("$V_A$ (V)")
    ax.set_ylabel("$V_Y$ (V)")
    ax.set_xticks([-5, 0, 5])
    ax.set_yticks([-5, 0, 5])
    ax.set_title("INV at taped-out W/L", loc="left")
    handles, labels = ax.get_legend_handles_labels()
    order = np.argsort([float(l.split("=")[1].split()[0]) for l in labels])
    ax.legend([handles[i] for i in order], [labels[i] for i in order], loc="lower left",
              handlelength=1.4)


def make():
    style.use()
    fig, axes = plt.subplots(1, 3, figsize=(style.DOUBLE, 2.35),
                             gridspec_kw={"width_ratios": [1, 1.25, 1.25], "wspace": 0.42})
    transfers(axes[0])
    axes[1].set_ylim(3, 3000)
    scatter(axes[1], "INV", floor_mv=3)
    axes[1].set_title("INV: 90 sizes, by resistor length", loc="left", pad=11)
    axes[1].set_ylabel("Worst level error (mV)")
    keys = [Line2D([], [], ls="", marker="o", ms=3.6, mfc=style.INK2, mec=style.INK2, label="passes"),
            Line2D([], [], ls="", marker="o", ms=3.6, mfc="white", mec=style.INK2, label="fails ±0.5 V"),
            Line2D([], [], ls="", marker="v", ms=3.6, mfc=style.INK2, mec=style.INK2, label="< 3 mV")]
    nany_n = sum(r["max_error_v"] is not None for r in grid("NANY")["rows"])
    scatter(axes[2], "NANY", limit=False)
    axes[2].set_ylim(bottom=0)
    axes[2].set_title(f"NANY: {nany_n} solved sizes, all pass", loc="left", pad=11)
    for ax, l in zip(axes, "abc"):
        style.panel(ax, l, x=-0.3)
    return style.save(fig, "fig_sizing")


if __name__ == "__main__":
    print(make())
