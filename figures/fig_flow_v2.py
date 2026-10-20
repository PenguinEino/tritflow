"""Fig. 1 (v2) — one ternary HDL source to a checked TR-1um layout, drawn from the real GDS."""

import io
import json

import klayout.db as db
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.patches import ConnectionPatch, FancyArrowPatch

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


def panel(fig, rect, title, note):
    """An axes with its title above and a two-line note below, in figure coordinates."""
    ax = fig.add_axes(rect)
    x, y, w, h = rect
    fig.text(x, y+h+0.045, title, fontsize=9, fontweight="bold", color=style.INK, va="bottom")
    fig.text(x, y-0.025, "\n".join(note), fontsize=7.4, color=style.INK2, va="top", linespacing=1.35)
    return ax


def arrow(fig, start, end, **options):
    fig.patches.append(FancyArrowPatch(start, end, transform=fig.transFigure, arrowstyle="-|>",
                                       mutation_scale=8, lw=0.8, color=style.INK2, **options))


def make():
    style.use()
    plt.rcParams["hatch.linewidth"] = 0.25
    report = json.loads((B/"adder4.report.json").read_text())
    pnr = json.loads((B/"adder4.pnr.json").read_text())
    lvs = json.loads((B/"adder4.lvs.summary.json").read_text())
    drc_items = pnr.get("checks", {}).get("pdk_drc", {}).get("violations") or 0
    fig = plt.figure(figsize=(style.DOUBLE, 5.1))

    # Top row: the source and what synthesis makes of it.
    top, height = 0.635, 0.29
    ax = panel(fig, [0.01, top, 0.2, height], "TritVerilog", ["four full adders in a chain", "+ full_add, half_add"])
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes, fc="#f6f5f1", ec=style.AXIS, lw=0.6))
    ax.text(0.06, 0.95, HDL, transform=ax.transAxes, family="monospace", fontsize=6.4, va="top",
            color=style.INK, linespacing=1.3)
    ax = panel(fig, [0.27, top, 0.72, height], "Synthesis",
               [f"{report['total_cells']} cells for the adder; one half adder at a = b = +1:",
                "1 + 1 = sum −1, carry +1 (red +1, blue −1, gray 0)"])
    ax.axis("off")
    half = flow.load(ROOT/"examples/half_add.tv", "half_add").synthesize()
    picture = plt.imread(io.BytesIO(half.schematic(inputs={"a": 1, "b": 1}, net_names=False, title="").png(scale=3)))
    picture = picture[int(picture.shape[0]*0.06):int(picture.shape[0]*0.78)]   # drop the cell count and legend
    ink = np.where((picture[..., :3] < 0.92).any(axis=2))
    picture = picture[ink[0].min():ink[0].max()+1, ink[1].min():ink[1].max()+1]
    ax.imshow(picture, interpolation="lanczos")
    ax.set_anchor("W")
    arrow(fig, (0.215, top+height/2), (0.262, top+height/2))

    # Bottom row: the cell it is built from, the routed layout, and the extracted circuit running.
    low, height = 0.11, 0.29
    ax = panel(fig, [0.01, low, 0.16, height], "Standard cell", ["NANY, from the taped-out", "circuit; 3 rails"])
    draw_gds(ax, CELLS_DIR/"out/NANY/NANY.gds", line=0.35)
    ax = panel(fig, [0.21, low, 0.2, height], "Place & route",
               [f"{pnr['die'][0]:.0f} × {pnr['die'][1]:.0f} µm, M1 + M2",
                f"DRC {drc_items}, LVS {'match' if lvs['matched'] else 'mismatch'}"])
    box = draw_gds(ax, B/"adder4.gds", line=0.08)
    # A corner next to the magnified view keeps the guide lines short.
    size = 0.28*box.width()
    x0, y0 = box.right-0.03*box.width()-size, box.bottom+0.35*box.height()
    ax.add_patch(plt.Rectangle((x0, y0), size, size, fill=False, ec="#eb6834", lw=0.9, zorder=10))
    zoom = panel(fig, [0.43, low, 0.2, height], "", ["magnified: transistors,", "M1, M2 and vias"])
    draw_gds(zoom, B/"adder4.gds", line=0.25)
    zoom.set_xlim(x0, x0+size)
    zoom.set_ylim(y0, y0+size)
    zoom.axis("on")
    zoom.set_xticks([])
    zoom.set_yticks([])
    for spine in zoom.spines.values():
        spine.set_edgecolor("#eb6834")
        spine.set_linewidth(0.9)
    fig.add_artist(ConnectionPatch((x0+size, y0+size), (0, 1), "data", "axes fraction", axesA=ax, axesB=zoom,
                                   color="#eb6834", lw=0.6, ls=":"))
    fig.add_artist(ConnectionPatch((x0+size, y0), (0, 0), "data", "axes fraction", axesA=ax, axesB=zoom,
                                   color="#eb6834", lw=0.6, ls=":"))

    ax = panel(fig, [0.7, low, 0.25, height], "Post-layout SPICE",
               ["extracted devices + wire C", "three levels, ±0.5 V bands"])
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

    middle = low+height/2
    # From the end of the top row, around the right margin and back to the start of the bottom row.
    turn = 0.537
    fig.add_artist(plt.Line2D([0.993, 0.993, 0.03], [top+height/2, turn, turn], transform=fig.transFigure,
                              color=style.INK2, lw=0.8))
    arrow(fig, (0.03, turn), (0.03, low+height+0.085))
    arrow(fig, (0.175, middle), (0.205, middle))
    arrow(fig, (0.645, middle), (0.69, middle))
    return style.save(fig, "fig_flow_v2")


if __name__ == "__main__":
    print(make())
