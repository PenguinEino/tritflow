# Brief: SCHEM_COMPACT — redraw the four taped-out cell schematics compactly, checked by eye

Work in the git worktree `~/code-a-chip-schem` (branch `schem-compact`). Never touch `~/code-a-chip`,
`~/code-a-chip-rewrite`, other worktrees, or `~/balanced-ternary-logic` (read it only). No git commit
or push: the integrator reviews and commits.

## Why

Chapter 3 of the v2 notebook (`notebook/v2/make_notebook.py`, cell "3-2", `notebook/cell_views.py`
`cell_tables`) shows, folded under the cells' truth tables, the taped-out Xschem schematics of INV,
NAND, NOR and NANY side by side in a grid. The taped-out drawings (`~/balanced-ternary-logic/
inverter.sch`, `mul_nand.sch`, `mul_nor.sch`, `nany.sch`) use long wires and wide margins: fine alone,
wasteful side by side. An automatic gap-closing pass (`notebook/v2/compact_schematics.py`, output
`notebook/assets/schematics/*.compact.svg`) did not help: the author judged the result "terrible, nothing
improved". The figures must be redrawn by hand, as a designer would, and checked by looking at them.

## What to make

For each of INV, NAND, NOR, NANY a new Xschem schematic `notebook/assets/schematics/src/<cell>.sch`
(replace the `*_compact.sch` files) and its SVG `notebook/assets/schematics/<CELL>.compact.svg`:

- Same circuit as the taped-out drawing: every device with its symbol (PDK `TR-1umLIB/MP.sym`, `MN.sym`,
  `RR.sym`), the same W/L/R parameters and the same connections, all ports (pins) and net labels. Keep
  labels and pins; do not reduce them. Body (BG) and RR SUB connections as in the originals (labels are
  fine where the original used wires to a rail, if clearer).
- Compact and tidy: devices close together on a regular grid, short straight wires, no wire running
  through text, no overlapping text, consistent spacing; the four figures drawn at the same scale with
  similar style (supply at top, ground at bottom, inputs on the left, output on the right). They must
  read well at about 480 px wide each in a 2-column grid.
- Prove the drawings are the same circuits: netlist each new .sch with Xschem (`xschem -n -s -q` or the
  batch netlist command) and compare device by device and net by net (up to net naming) with a netlist
  of the taped-out drawing. Report it.
- Export SVG the way `notebook/v2/compact_schematics.py` `export` does (Xschem batch print with an exact
  box, `notebook/export_schematics._theme_svg`, serif face). Update or replace
  `compact_schematics.py` so it regenerates the SVGs from your hand-drawn .sch files (no automatic
  compaction any more).

## Check every iteration by eye

You cannot see the page unless you render it. After every change:
1. Render each SVG to PNG (e.g. `python3 -c "import cairosvg; cairosvg.svg2png(...)"` or headless Chrome
   `google-chrome --headless=new --no-sandbox --screenshot=out.png --window-size=W,H file://...`).
2. Open and look at the PNG images (use your image viewing ability on the files) and critique them like
   a picky reviewer: overlaps, cramped or wasted space, crossing wires, alignment, legibility at 480 px.
3. Also render chapter 3's actual output: build the notebook (`python3 notebook/v2/make_notebook.py
   --out build/v2/local.ipynb`), execute it with nbclient (see how `build/v2` runs are done: set
   `TR1UM_PDK=~/pdk/TR-1um-pinned TRITFLOW_ROOT=~/code-a-chip-schem`), extract the HTML output of the
   cell starting with `# 3-2`, change `<details>` to `<details open>`, screenshot it with headless Chrome
   at 1100 px wide, and look at it.
Iterate until you would be happy to put the figure in a paper. Keep the final screenshots under
`build/schem-compact/` and list them in your status note.

## Rules

- TR1UM_PDK=~/pdk/TR-1um-pinned; Xschem library path: the PDK's `libs.tech/xschem` and
  `/usr/local/share/xschem/xschem_library`.
- Edit only `notebook/assets/schematics/`, `notebook/v2/compact_schematics.py`, and, if needed for the
  grid layout, `notebook/cell_views.py` (`cell_tables` only). Keep chapter 2's
  `notebook/assets/schematics/src/inv_compact.sch` untouched.
- No new dependencies, no network services, no publishing, no sign-in.
- Write `docs/status/SCHEM_COMPACT.md`: what you drew, the netlist equivalence evidence, the screenshots,
  and what you would still improve.
