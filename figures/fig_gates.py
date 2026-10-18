"""Fig. 2 — DC behaviour of the four logic cells (extracted layouts, nominal 27 °C)."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from tritflow import ROOT
from tritflow.sim import dc_transfer

import style
from matplotlib.offsetbox import AnchoredOffsetbox, HPacker, TextArea

# Swept input A is the x axis, output Y the y axis; the curve colour is the value of B.
A_COLOR, Y_COLOR = "#6250d6", "#0f6e56"
B_TEXT = {-1: "−1", 0: "0", 1: "+1"}
CELLS = [("INV", [("−", None), ("A", A_COLOR)]),
         ("NAND", [("−min(", None), ("A", A_COLOR), (", ", None), ("B", "B"), (")", None)]),
         ("NOR", [("−max(", None), ("A", A_COLOR), (", ", None), ("B", "B"), (")", None)]),
         ("NANY", [("−sat(", None), ("A", A_COLOR), (" + ", None), ("B", "B"), (")", None)])]


def colored_row(ax, pieces, y, size=8):
    """Place a left-aligned run of differently coloured text above an axes."""
    boxes = [TextArea(t, textprops=dict(color=c or style.INK, size=size,
                                        weight="bold" if c not in (None, style.INK2) else "normal"))
             for t, c in pieces]
    row = HPacker(children=boxes, align="baseline", pad=0, sep=0)
    ax.add_artist(AnchoredOffsetbox(loc="lower left", child=row, pad=0, borderpad=0, frameon=False,
                                    bbox_to_anchor=(0, y), bbox_transform=ax.transAxes))


def sweep(cell, b):
    spice = (ROOT / f"cells/out/{cell}/{cell}.ext.spice").read_text()
    inputs = ["A"] if cell == "INV" else ["A", "B"]
    fixed = {} if cell == "INV" else {"B": b}
    d = dc_transfer(spice, cell, inputs, ["Y"], "A", fixed_trits=fixed, step_v=0.02)["data"]
    return d["v-sweep"], d["v(y)"], np.abs(d["i(vdd)"]) * 1e3


def make():
    style.use()
    fig, axes = plt.subplots(2, 4, figsize=(style.DOUBLE, 3.35), sharex=True,
                             gridspec_kw={"height_ratios": [1.35, 1], "hspace": 0.12, "wspace": 0.32})
    for col, (cell, fn) in enumerate(CELLS):
        top, bot = axes[0, col], axes[1, col]
        style.bands(top)
        for b in ([0] if cell == "INV" else [-1, 0, 1]):
            x, y, i = sweep(cell, b)
            color = style.INK if cell == "INV" else style.TRIT_COLOR[b]
            label = None if cell == "INV" else f"B = {['−1','0','+1'][b+1]}"
            top.plot(x, y, color=color, lw=1.1, label=label)
            bot.plot(x, i, color=color, lw=1.1)
        formula = [(t, (style.INK if c == "B" else c)) for t, c in fn]
        colored_row(top, [(f"{cell}:  ", None), ("Y", Y_COLOR), (" = ", None)] + formula, 1.13)
        if cell != "INV":
            key = [("B = ", style.INK2)]
            for b in (-1, 0, 1):
                key += [(B_TEXT[b], style.TRIT_COLOR[b]), ("   " if b < 1 else "", style.INK2)]
            colored_row(top, key, 1.02, size=7)
        top.set_ylim(-5.6, 5.6)
        top.set_yticks([-5, 0, 5])
        bot.set_ylim(bottom=0)
        bot.set_xticks([-5, 0, 5])
        bot.set_xlabel("$V_A$ (V)", color=A_COLOR)
        if col == 0:
            top.set_ylabel("$V_Y$ (V)", color=Y_COLOR)
            bot.set_ylabel("$|I_{VDD}|$ (mA)")
    style.panel(axes[0, 0], "a", x=-0.36, y=1.13)
    style.panel(axes[1, 0], "b", x=-0.36)
    axes[0, 0].text(-4.9, -4.15, "shaded: ±0.5 V bands", fontsize=6.5, color=style.INK2)
    return style.save(fig, "fig_gates")


if __name__ == "__main__":
    print(make())
