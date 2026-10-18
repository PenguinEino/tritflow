"""Fig. 9 — N-trit ripple adders generated from one HDL source: delay, idle power, area."""

import matplotlib.pyplot as plt
import numpy as np

import data
import style


def rows():
    d = data.load("results/adder_scaling.json")
    out = [r for r in d["rows"] if r.get("state") == "complete"]
    if len(out) != len(d["rows"]):
        raise SystemExit("adder_scaling.json is incomplete; set FIG_REF to a committed snapshot")
    return out


def fit(x, y):
    k, b = np.polyfit(x, y, 1)
    return k, b


def make():
    style.use()
    rs = rows()
    n = np.array([r["n"] for r in rs])
    pre = np.array([r["carry"]["pre"]["max_settling_s"] for r in rs]) * 1e9
    post = np.array([r["carry"]["post"]["max_settling_s"] for r in rs]) * 1e9
    p_worst = np.array([r["static_power_worst_w"] for r in rs]) * 1e3
    cells = np.array([r["cell_count"] for r in rs])
    area = np.array([r["die_area_um2"] for r in rs]) * 1e-6

    fig, axes = plt.subplots(1, 3, figsize=(style.DOUBLE, 2.15), gridspec_kw={"wspace": 0.42})

    ax = axes[0]
    for y, c, lab in ((pre, style.BLUE, "schematic"), (post, style.ORANGE, "extracted layout")):
        k, b = fit(n, y)
        xs = np.linspace(0.6, 6.4, 2)
        ax.plot(xs, k * xs + b, color=c, lw=0.8, alpha=0.6)
        ax.plot(n, y, "o", ms=4, color=c, mec="white", mew=0.6, label=f"{lab}: {k:.1f} ns/trit")
    ax.set_xlabel("Adder width $N$ (trits)")
    ax.set_ylabel("Worst carry settling (ns)")
    ax.set_ylim(bottom=0)
    ax.legend(loc="upper left", handletextpad=0.2)

    ax = axes[1]
    k, b = fit(cells, p_worst)
    xs = np.linspace(0, cells.max() * 1.05, 2)
    ax.plot(xs, k * xs + b, color=style.INK2, lw=0.8, ls=(0, (3, 2)))
    ax.plot(cells, p_worst, "o", ms=4, color=style.INK, mec="white", mew=0.6)
    for x, y, nn in zip(cells, p_worst, n):
        ax.annotate(f"N={nn}", (x, y), xytext=(-4, 5), textcoords="offset points",
                    fontsize=6.5, color=style.INK2, ha="right")
    ax.text(0.97, 0.06, f"{k:.2f} mW per cell", transform=ax.transAxes, ha="right",
            fontsize=7, color=style.INK)
    ax.set_xlabel("Cells")
    ax.set_ylabel("Idle supply power, worst input (mW)")
    ax.set_xlim(0, cells.max() * 1.08)
    ax.set_ylim(0, p_worst.max() * 1.15)

    ax = axes[2]
    ax.bar(n, area, width=0.62, color=style.BLUE, edgecolor="white", linewidth=0.6)
    for x, a, c in zip(n, area, cells):
        ax.text(x, a + area.max() * 0.02, f"{c}", ha="center", va="bottom", fontsize=6.5,
                color=style.INK2)
    ax.text(0.03, 0.97, "labels: cell count", transform=ax.transAxes, va="top", fontsize=6.5,
            color=style.INK2)
    ax.set_xlabel("Adder width $N$ (trits)")
    ax.set_ylabel("Die area (mm$^2$)")
    ax.set_ylim(0, area.max() * 1.18)
    ax.grid(axis="x", visible=False)

    for a in axes[[0, 2]]:
        a.set_xticks(n)
    for ax, l in zip(axes, "abc"):
        style.panel(ax, l, x=-0.3)
    return style.save(fig, "fig_scaling")


if __name__ == "__main__":
    print(make())
