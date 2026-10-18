"""Regenerate every paper figure into figures/out/ (PDF, PNG, SVG).

    PYTHONPATH=. python3 figures/make_all.py            # live results
    FIG_REF=<commit> PYTHONPATH=. python3 figures/make_all.py   # committed results/ snapshot
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fig_cell  # noqa: E402
import fig_flow  # noqa: E402
import fig_gates  # noqa: E402
import fig_pnr  # noqa: E402
import fig_postlayout  # noqa: E402
import fig_scaling  # noqa: E402
import fig_sizing  # noqa: E402
import fig_sta  # noqa: E402
import fig_synth  # noqa: E402

for module in (fig_flow, fig_gates, fig_sizing, fig_cell, fig_synth, fig_pnr, fig_postlayout, fig_scaling, fig_sta):
    print(module.make())
