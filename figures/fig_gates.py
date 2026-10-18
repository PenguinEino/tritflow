"""Fig. 2 — DC behaviour of the four logic cells (extracted layouts, nominal 27 °C)."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from tritflow import ROOT
from tritflow.sim import dc_transfer

import style

CELLS = [("INV", "−A"), ("NAND", "−min(A,B)"), ("NOR", "−max(A,B)"), ("NANY", "−sat(A+B)")]


def sweep(cell, b):
    spice = (ROOT / f"cells/out/{cell}/{cell}.ext.spice").read_text()
    inputs = ["A"] if cell == "INV" else ["A", "B"]
    fixed = {} if cell == "INV" else {"B": b}
    d = dc_transfer(spice, cell, inputs, ["Y"], "A", fixed_trits=fixed, step_v=0.02)["data"]
    return d["v-sweep"], d["v(y)"], np.abs(d["i(vdd)"]) * 1e3


def make():
    style.use()
    fig, axes = plt.subplots(2, 4, figsize=(style.DOUBLE, 3.15), sharex=True,
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
        top.set_title(f"{cell}:  Y = {fn}", loc="left", fontsize=8, color=style.INK)
        top.set_ylim(-5.6, 5.6)
        top.set_yticks([-5, 0, 5])
        bot.set_ylim(bottom=0)
        bot.set_xticks([-5, 0, 5])
        bot.set_xlabel("$V_A$ (V)")
        if col == 0:
            top.set_ylabel("$V_Y$ (V)")
            bot.set_ylabel("$|I_{VDD}|$ (mA)")
        if cell == "NAND":
            top.legend(loc="lower left", handlelength=1.4, borderaxespad=0.2)
    style.panel(axes[0, 0], "a", x=-0.36)
    style.panel(axes[1, 0], "b", x=-0.36)
    axes[0, 0].text(-4.9, -4.15, "shaded: ±0.5 V bands", fontsize=6.5, color=style.INK2)
    return style.save(fig, "fig_gates")


if __name__ == "__main__":
    print(make())
