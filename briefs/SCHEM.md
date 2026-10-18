# Brief: SCHEM stream — clean schematics as a pipeline stage

You own `tritflow/schematic/`, `tests/schematic/`, `docs/status/SCHEM.md`. Read `AGENTS.md`,
`docs/interfaces.md`, `docs/editorial.md` (style), `figures/style.py` (paper palette) first.

## Goal
Right after synthesis, the flow produces a readable, good-looking schematic of the synthesized
netlist, the way a designer would draw it by hand — not a graph dump. It is a stage of the
pipeline: `net = design.synthesize(); sch = net.schematic(); sch.svg / sch.pdf / sch.show()`,
and the notebook shows it between synthesis and P&R. Later stages reuse it (values, parasitics).

## Requirements
1. Symbols: a consistent ternary gate symbol set drawn like textbook logic symbols: INV (triangle +
   bubble), NAND (−min) and NOR (−max) using the familiar NAND/NOR outlines, NANY (−sat(a+b))
   with a distinct but equally clean shape, BUF, TIE cells as supply-style symbols (+1/0/−1), and
   ports. Document the symbol legend (one figure) and why each shape was chosen.
2. Layout: left-to-right signal flow (layered placement), crossing minimisation, orthogonal
   (Manhattan) wiring with proper channel routing between columns, junction dots at T-joins,
   no wire through a symbol, no overlapping labels, grid-aligned. Inputs on the left, outputs on
   the right, bit vectors ordered.
3. Hierarchy: use the instance hierarchy kept by synthesis (e.g. `digit[1].fa.ha2`). Default view
   draws each module instance as a labelled block with its ports; `expand=` selects which
   instances are drawn at cell level; a full flat view must also stay readable for the full adder.
4. Annotations (optional overlays on the same drawing): trit value per net for an input vector
   (colour encoding −1 blue / 0 grey / +1 red from figures/style.py), net names, and per-net wire
   capacitance once PNR publishes `PnrResult.net_parasitics()` (thicker/darker = more C, with fF labels).
5. Output: SVG (default, crisp in Colab and GitHub) and PDF; deterministic. Pure Python with no
   new system dependencies that are missing on Colab (plain SVG writing is preferred; Graphviz only
   if you can make it look equally clean and it is available on Colab).
6. Quality bar: render half_add, full_add, adder N=2 and N=4 (hierarchical and flat), mul1, mac1
   and the curated chapter-8 designs; inspect every PNG yourself and iterate until a circuit designer
   would accept them in a paper. Tests check determinism, no symbol overlap, no wire-through-symbol,
   and that every netlist connection appears exactly once in the drawing.
7. Integrate through public APIs only: add the method via a small hook FRONTEND can call
   (`tritflow.schematic.draw(netlist, ...)`); write an Interface request in your status file for the
   one-line `schematic()` delegate in FRONTEND's netlist class and the notebook cell.
