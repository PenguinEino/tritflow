"""Fig. 4 — from the taped-out NANY to an abuttable three-rail standard cell."""

from pathlib import Path

import matplotlib.pyplot as plt

from tritflow import CELLS_DIR, ROOT
from tritflow.viz.cell import device_locations

import gdsdraw
import style

ORIGINAL = Path.home() / "balanced-ternary-logic" / "nany.gds"
ROW = ("INV", "NAND", "NOR", "NANY")


def cell_gds(name):
    return CELLS_DIR / "out" / name / f"{name}.gds"


def add_axes(fig, x, y, w_um, h_um, scale):
    """Axes at (x, y) inches whose data units are µm at `scale` inch/µm."""
    W, H = fig.get_size_inches()
    return fig.add_axes([x / W, y / H, w_um * scale / W, h_um * scale / H])


def annotate_devices(ax):
    rows = {r["schematic_name"]: r["bbox_um"] for r in device_locations("NANY")}
    groups = [
        (("XM5", "XM3"), "pull-up"),
        (("XM2", "XM1"), "pull-down"),
        (("XM6", "XM8"), "clamp"),
        (("XM7", "XM9"), "clamp"),
        (("R2", "R1"), "$R$ 2.8/30 µm"),
    ]
    for names, label in groups:
        boxes = [rows[n] for n in names]
        x0 = min(b[0] for b in boxes) - 1.5
        x1 = max(b[2] for b in boxes) + 1.5
        y0 = min(b[1] for b in boxes) - 1.5
        y1 = max(b[3] for b in boxes) + 1.5
        ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, lw=0.7,
                                   ec=style.INK, ls=(0, (2, 1.5)), zorder=20))
        above = label != "pull-down" and not (label == "clamp" and y0 < 60)
        ax.text((x0 + x1) / 2, y1 + 1.5 if above else y0 - 1.5, label, ha="center",
                va="bottom" if above else "top", fontsize=6.5, color=style.INK, zorder=21,
                bbox=dict(boxstyle="square,pad=0.1", fc="white", ec="none", alpha=0.85))


def rail_labels(ax, x, template):
    va = {"VDD": "center", "VMID": "bottom", "VSS": "top"}
    for name, (y0, y1) in template["rails"].items():
        y = {"VDD": (y0 + y1) / 2, "VMID": y0, "VSS": y1}[name]
        ax.text(x, y, name, ha="left", va=va[name], fontsize=6.5, color=style.INK)


def make():
    import json
    style.use()
    template = json.loads((CELLS_DIR / "template.json").read_text())
    fig = plt.figure(figsize=(style.DOUBLE, 3.95))
    s1 = 0.0118

    ax = add_axes(fig, 0.25, 1.95, 152, 119, s1)
    bb = gdsdraw.draw(ax, ORIGINAL)
    gdsdraw.frame(ax, bb)
    ax.set_title("taped-out NANY (148 × 115 µm)", loc="left", pad=3)
    style.panel(ax, "a", x=-0.08, y=1.03)

    ax = add_axes(fig, 2.25, 1.95, 172, 136, s1)
    bb = gdsdraw.draw(ax, cell_gds("NANY"))
    gdsdraw.frame(ax, bb)
    annotate_devices(ax)
    rail_labels(ax, bb.right + 2.5, template)
    ax.set_xlim(right=bb.right + 22)
    ax.set_title(f"standard-cell NANY ({bb.width():.0f} × {bb.height():.0f} µm)", loc="left", pad=3)
    style.panel(ax, "b", x=-0.08, y=1.03)

    lax = fig.add_axes([0.70, 0.50, 0.28, 0.45])
    lax.axis("off")
    lax.legend(handles=gdsdraw.legend_handles(), loc="upper left", ncol=1, handlelength=1.6,
               handleheight=0.9, title="TR-1um drawing layers", title_fontsize=7, alignment="left")

    s2 = 0.0112
    total = 0.0
    widths = []
    for name in ROW:
        a = json.loads((CELLS_DIR / "out" / name / f"{name}.abstract.json").read_text())
        widths.append(a["width"])
        total += a["width"]
    ax = add_axes(fig, 0.25, 0.12, total + 24, 140, s2)
    x = 0.0
    for name, w in zip(ROW, widths):
        gdsdraw.draw(ax, cell_gds(name), dx=x, rasterized=False)
        ax.axvline(x, color=style.INK2, lw=0.5, ls=(0, (1, 1.5)), zorder=30)
        ax.text(x + w / 2, template["height"] + 3, name, ha="center", va="bottom", fontsize=7)
        x += w
    ax.axvline(x, color=style.INK2, lw=0.5, ls=(0, (1, 1.5)), zorder=30)
    rail_labels(ax, x + 3, template)
    ax.set_xlim(-2, x + 24)
    ax.set_ylim(-3, template["height"] + 12)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.text(0, -3, "abutted row: VDD, VMID and VSS rails run continuously across cell boundaries (dotted)",
            fontsize=6.5, color=style.INK2, va="top")
    style.panel(ax, "c", x=-0.02, y=0.98)
    return style.save(fig, "fig_cell")


if __name__ == "__main__":
    print(make())
