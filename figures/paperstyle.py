"""Shared paper style for TritFlow figures (IEEE-like, print-first)."""

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

OUT = Path(__file__).resolve().parent / "out"

# Column widths of an IEEE two-column page, inches.
SINGLE = 3.5
DOUBLE = 7.16

INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"

# Categorical (validated: CVD ΔE ≥ 9.2 adjacent; aqua needs direct labels).
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
# Diverging trit encoding: −1 cool, 0 neutral, +1 warm.
TRIT_COLOR = {-1: "#2a78d6", 0: "#6f6e69", 1: "#e34948"}
TRIT_FILL = {-1: "#cde2fb", 0: "#ecebe6", 1: "#f7d3d2"}
BAND = "#ecebe6"  # ±0.5 V acceptance bands


def use():
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Nimbus Roman", "Liberation Serif", "DejaVu Serif"],
        "mathtext.fontset": "stix",
        "font.size": 8,
        "axes.titlesize": 8,
        "axes.labelsize": 8,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 7,
        "axes.edgecolor": INK2,
        "axes.labelcolor": INK,
        "axes.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "axes.axisbelow": True,
        "xtick.color": INK2,
        "ytick.color": INK2,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.major.size": 2.5,
        "ytick.major.size": 2.5,
        "lines.linewidth": 1.2,
        "lines.solid_capstyle": "round",
        "legend.frameon": False,
        "figure.dpi": 150,
        "savefig.dpi": 600,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.02,
        "pdf.fonttype": 42,
        "svg.fonttype": "none",
        "svg.hashsalt": "tritflow",
    })


def panel(ax, letter, x=-0.16, y=1.04):
    """IEEE-style panel tag: (a), (b), ..."""
    ax.text(x, y, f"({letter})", transform=ax.transAxes, fontsize=8,
            fontweight="bold", va="bottom", ha="left", color=INK)


def bands(ax, levels=(-5, 0, 5), half=0.5, horizontal=True):
    for v in levels:
        if horizontal:
            ax.axhspan(v - half, v + half, color=BAND, lw=0, zorder=0)
        else:
            ax.axvspan(v - half, v + half, color=BAND, lw=0, zorder=0)


def save(fig, name, out=None):
    out = Path(out) if out is not None else OUT
    out.mkdir(parents=True, exist_ok=True)
    meta = {"pdf": {"CreationDate": None, "ModDate": None}, "svg": {"Date": None}, "png": {}}
    for ext in ("pdf", "png", "svg"):
        fig.savefig(out / f"{name}.{ext}", metadata=meta[ext])
    plt.close(fig)
    return out / f"{name}.png"
