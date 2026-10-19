"""Fig. 1 — TritFlow at a glance: one HDL source to a checked, simulated TR-1um layout (4-trit adder)."""

import json

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch

from tritflow import CELLS_DIR, ROOT

import gdsdraw
import paperstyle as style

B = ROOT / "build/adder4"
HDL = """generate
 for (i=0; i<N; i=i+1)
 begin : digit
  full_add fa (
   .a(a[i]), .b(b[i]),
   .cin(c[i]),
   .sum(sum[i]),
   .cout(c[i+1]));
 end
endgenerate"""


def stage_axes(fig, i, n, top=0.84, bottom=0.30, gap=0.035):
    w = (1 - gap * (n + 1)) / n
    return fig.add_axes([gap + i * (w + gap), bottom, w, top - bottom])


def caption(fig, ax, title, lines):
    pos = ax.get_position()
    x = pos.x0
    fig.text(x, 0.95, title, fontsize=9, fontweight="bold", color=style.INK, va="top")
    fig.text(x, 0.2, "\n".join(lines), fontsize=7.6, color=style.INK2, va="top",
             linespacing=1.35)


def arrows(fig, axes):
    for a, b in zip(axes, axes[1:]):
        pa, pb = a.get_position(), b.get_position()
        y = (pa.y0 + pa.y1) / 2
        fig.patches.append(FancyArrowPatch((pa.x1 + 0.004, y), (pb.x0 - 0.004, y),
                                           transform=fig.transFigure, arrowstyle="-|>",
                                           mutation_scale=8, lw=0.8, color=style.INK2))


def make():
    style.use()
    report = json.loads((B / "adder4.report.json").read_text())
    pnr = json.loads((B / "adder4.pnr.json").read_text())
    lvs = json.loads((B / "adder4.lvs.summary.json").read_text())
    drc_items = pnr.get("checks", {}).get("pdk_drc", {}).get("violations")
    template = json.loads((CELLS_DIR / "template.json").read_text())
    die = pnr["die"]

    fig = plt.figure(figsize=(style.DOUBLE, 2.45))
    axes = [stage_axes(fig, i, 5) for i in range(5)]

    ax = axes[0]
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, fc="#f6f5f1", ec=style.AXIS,
                               lw=0.6))
    ax.text(0.05, 0.95, HDL, transform=ax.transAxes, family="monospace", fontsize=6.3, va="top",
            color=style.INK, linespacing=1.3)
    caption(fig, ax, "TritVerilog", [f"adder #(N = 4): {len((ROOT / 'examples/adder.tv').read_text().splitlines())} lines",
                                     "+ full_add, half_add modules"])

    ax = axes[1]
    ax.axis("off")
    counts = report["cells"]
    names = sorted(counts, key=lambda k: -counts[k])
    ax.barh(range(len(names)), [counts[k] for k in names], color=style.BLUE, height=0.38)
    for i, k in enumerate(names):
        ax.text(counts[k] + 0.8, i, f"{k}  {counts[k]}", va="center", fontsize=8)
    ax.set_xlim(0, max(counts.values()) * 1.8)
    ax.set_ylim(-0.8, len(names) - 0.2)
    ax.invert_yaxis()
    caption(fig, ax, "Synthesis", [f"{report['total_cells']} cells, depth {report['logic_depth']}",
                                   f"equivalence: {report['equivalence'].get('mode', 'checked')}"
                                   if isinstance(report.get("equivalence"), dict) else "equivalence checked"])

    ax = axes[2]
    bb = gdsdraw.draw(ax, CELLS_DIR / "out/NANY/NANY.gds", lw=0.15)
    gdsdraw.frame(ax, bb, pad=3)
    caption(fig, ax, "Standard cells", [f"9 cells from taped-out circuits",
                                        f"{template['height']:.0f} µm tall, three rails"])

    ax = axes[3]
    bb = gdsdraw.draw(ax, B / "adder4.gds", rasterized=True, lw=0.0)
    gdsdraw.frame(ax, bb, pad=10)
    drc = "0 DRC markers" if drc_items in (0, None) else f"{drc_items} DRC markers"
    caption(fig, ax, "Place & route", [f"{die[0]:.0f} × {die[1]:.0f} µm, M1 + M2",
                                       f"{drc}, LVS {'match' if lvs['matched'] else 'mismatch'}"])

    ax = axes[4]
    z = np.load(B / "postlayout/post/waveforms.npz")
    t = z["time"] * 1e6
    style.bands(ax)
    ax.plot(t, z["v(sum[3])"], color=style.BLUE, lw=0.8, label="sum[3]")
    ax.plot(t, z["v(cout)"], color=style.ORANGE, lw=0.8, label="cout")
    ax.set_yticks([-5, 0, 5])
    ax.set_ylim(-6, 6)
    ax.set_xticklabels([])
    ax.yaxis.tick_right()
    ax.tick_params(labelsize=6)
    ax.set_xlim(t[0], t[-1])
    caption(fig, ax, "Post-layout SPICE", ["sum[3] (blue), cout (orange), 0–%.0f µs" % t[-1],
                                           "extracted devices + wire C"])

    arrows(fig, axes)
    return style.save(fig, "fig_flow")


if __name__ == "__main__":
    print(make())
