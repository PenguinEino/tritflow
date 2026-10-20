"""Fig. 1 (v2) — one ternary HDL source to a checked TR-1um layout, drawn from the real GDS."""

import io
import json

import klayout.db as db
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.patches import FancyArrowPatch

from tritflow import CELLS_DIR, ROOT, flow
from tritflow.viz.layers import LAYER_STYLE, MATPLOTLIB_HATCH

import paperstyle as style

B = ROOT / "build/adder4"
HDL = """full_add fa0(
  a[0],b[0],cin,
  sum[0],c1);
full_add fa1(
  a[1],b[1],c1,
  sum[1],c2);
full_add fa2(
  a[2],b[2],c2,
  sum[2],c3);
full_add fa3(
  a[3],b[3],c3,
  sum[3],cout);"""


def draw_gds(ax, path, *, line=0.3):
    """Every drawn layer of a GDS, flattened, in the notebook's TR-1um colors and hatches."""
    layout = db.Layout()
    layout.read(str(path))
    top = layout.top_cells()[0]
    for key, _, color, hatch, opacity in LAYER_STYLE:
        index = layout.find_layer(*key)
        if index is None:
            continue
        region = db.Region(top.begin_shapes_rec(index)).merged()
        polygons = [[(p.x*layout.dbu, p.y*layout.dbu) for p in
                     (poly.to_simple_polygon().each_point() if poly.holes() else poly.each_point_hull())]
                    for poly in region.each()]
        if not polygons:
            continue
        if opacity:
            ax.add_collection(PolyCollection(polygons, facecolors=color, alpha=opacity, linewidths=0))
        ax.add_collection(PolyCollection(polygons, facecolors="none", edgecolors=color, linewidths=line,
                                         hatch=MATPLOTLIB_HATCH[hatch]))
    box = top.dbbox()
    ax.set_xlim(box.left, box.right)
    ax.set_ylim(box.bottom, box.top)
    ax.set_aspect("equal")
    ax.axis("off")
    return box


def make():
    style.use()
    plt.rcParams["hatch.linewidth"] = 0.25
    report = json.loads((B/"adder4.report.json").read_text())
    pnr = json.loads((B/"adder4.pnr.json").read_text())
    lvs = json.loads((B/"adder4.lvs.summary.json").read_text())
    drc_items = pnr.get("checks", {}).get("pdk_drc", {}).get("violations") or 0

    fig = plt.figure(figsize=(style.DOUBLE, 2.5))
    widths, gap, x = [0.14, 0.22, 0.15, 0.2, 0.14], 0.03, 0.012
    axes = []
    for width in widths:
        axes.append(fig.add_axes([x, 0.27, width, 0.6]))
        x += width+gap
    titles = ["TritVerilog", "Synthesis", "Standard cell", "Place & route", "Post-layout SPICE"]
    notes = [["four full adders in a chain", "+ full_add, half_add"],
             [f"{report['total_cells']} cells; one half adder:", "1 + 1 = sum −1, carry +1"],
             ["NANY, from the taped-out", "circuit; 3 rails"],
             [f"{pnr['die'][0]:.0f} × {pnr['die'][1]:.0f} µm, M1 + M2",
              f"DRC {drc_items}, LVS {'match' if lvs['matched'] else 'mismatch'}"],
             ["extracted devices + wire C", "three levels, ±0.5 V bands"]]
    for ax, title, note in zip(axes, titles, notes):
        x = ax.get_position().x0
        fig.text(x, 0.95, title, fontsize=9, fontweight="bold", color=style.INK, va="top")
        fig.text(x, 0.2, "\n".join(note), fontsize=7.4, color=style.INK2, va="top", linespacing=1.35)

    ax = axes[0]
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, fc="#f6f5f1", ec=style.AXIS, lw=0.6))
    ax.text(0.06, 0.95, HDL, transform=ax.transAxes, family="monospace", fontsize=5.9, va="top",
            color=style.INK, linespacing=1.3)

    # The synthesized half adder with a = b = +1, colored by settled trit (TritFlow's own schematic).
    ax = axes[1]
    ax.axis("off")
    half = flow.load(ROOT/"examples/half_add.tv", "half_add").synthesize()
    picture = plt.imread(io.BytesIO(half.schematic(inputs={"a": 1, "b": 1}, net_names=False, title="").png(scale=3)))
    picture = picture[int(picture.shape[0]*0.06):int(picture.shape[0]*0.78)]   # drop the cell count and legend
    ink = np.where((picture[..., :3] < 0.92).any(axis=2))
    picture = picture[ink[0].min():ink[0].max()+1, ink[1].min():ink[1].max()+1]
    ax.imshow(picture, interpolation="lanczos")
    ax.set_anchor("W")

    draw_gds(axes[2], CELLS_DIR/"out/NANY/NANY.gds", line=0.35)

    # Whole routed adder, with a magnified corner so devices and wires are visible.
    ax = axes[3]
    box = draw_gds(ax, B/"adder4.gds", line=0.08)
    ax.set_anchor("NW")
    x0, y0, size = box.left+0.02*box.width(), box.bottom+0.03*box.height(), 0.3*box.width()
    ax.add_patch(plt.Rectangle((x0, y0), size, size, fill=False, ec="#eb6834", lw=0.9, zorder=10))
    inset = ax.inset_axes([0.5, 0.0, 0.5, 0.5])
    draw_gds(inset, B/"adder4.gds", line=0.25)
    inset.set_xlim(x0, x0+size)
    inset.set_ylim(y0, y0+size)
    inset.axis("on")
    inset.set_xticks([])
    inset.set_yticks([])
    for spine in inset.spines.values():
        spine.set_edgecolor("#eb6834")
        spine.set_linewidth(0.9)
    inset.set_facecolor("white")

    # A short window in which the outputs visit all three levels.
    ax = axes[4]
    z = np.load(B/"postlayout/post/waveforms.npz")
    t = z["time"]*1e6
    window = t <= 3.2
    style.bands(ax)
    ax.plot(t[window], z["v(sum[3])"][window], color=style.BLUE, lw=0.9)
    ax.plot(t[window], z["v(cout)"][window], color=style.ORANGE, lw=0.9)
    ax.set_yticks([-5, 0, 5], ["−1", "0", "+1"])
    ax.yaxis.tick_right()
    ax.set_ylim(-6.5, 6.5)
    ax.tick_params(labelsize=7, length=0)
    ax.set_xticks([])
    ax.set_xlim(0, 3.2)
    ax.text(3.15, -6.2, "3 µs", fontsize=6, color=style.INK2, ha="right")
    ax.text(0.05, 6.0, "sum[3]", fontsize=6, color=style.BLUE)
    ax.text(1.1, 6.0, "cout", fontsize=6, color=style.ORANGE)

    for a, b in zip(axes, axes[1:]):
        pa, pb = a.get_position(), b.get_position()
        y = (pa.y0+pa.y1)/2
        fig.patches.append(FancyArrowPatch((pa.x1+0.004, y), (pb.x0-0.004, y), transform=fig.transFigure,
                                           arrowstyle="-|>", mutation_scale=8, lw=0.8, color=style.INK2))
    return style.save(fig, "fig_flow_v2")


if __name__ == "__main__":
    print(make())
