# FIGSYNTH brief: redraw figures/fig_synth.py (chapter-4 hero)

Owner paths: figures/fig_synth.py (and a figures-only helper if needed). Do not edit notebook/, tritflow/schematic/.

User feedback on the current figures/out/fig_synth.png: "lines cross, heights are uneven and not aligned, ugly."
Panel (b) uses curved Bezier wires, wires cross (a/b fan-out into INV and NANY; the NANY->NANY->NANY chain
has bundles of overlapping red/grey/blue curves; carry leaves from the middle of the chain), and boxes sit at
three arbitrary heights. Panel (c) also mixes curves and placement heights.

Required redesign (paper-quality, matplotlib, deterministic via figures/style.py save):
- Orthogonal (Manhattan) wiring only, with junction dots at branches; zero wire crossings in (b) and (c) if
  topologically possible, otherwise at most one crossing drawn with a clear hop/gap.
- Cells on a strict grid: columns = logic level, rows aligned; all cell boxes identical size per type; inputs on a common left
  x, outputs on a common right x, sum/carry ports vertically aligned. Use the actual half_add netlist from
  examples/half_add.tv (gates g_t, g_u, g_na, g_c, g_d, g_nd, g_s) -- label each box with its instance name and cell type
  (e.g. "g_t / NANY"), and draw pins so each input wire lands on a distinct pin.
- Panel (c) full_add: ha1, ha2 blocks same size, top-aligned on one row grid, carry merge (g_nc NANY, g_cout INV) aligned,
  straight horizontal sum path; no curved wires.
- Keep the trit net colours (style.TRIT_COLOR) and legend, the a=b=+1 example values, the titles with the identity
  2 = (−1) + 3·(+1), and panel (a) code text. Values must stay data-driven (cell counts from figures/data.py as now).
- Font sizes consistent with other figures; legible at the 100%-width notebook embed (~1000 px).
Visual loop: render figures/out/fig_synth.png, VIEW the image, list defects, fix, repeat until there are no crossings, no
overlaps and everything is aligned. Regenerate only this figure (e.g. run fig_synth.py the way figures/make_all.py does) and any figure tests
(pytest figures tests -k synth if present). Record before/after notes in docs/status/FIGSYNTH.md. Do not commit.
