# Brief: SCHEM_ROUTE — the gate-level schematic must draw every synthesized netlist

Work in the git worktree `~/code-a-chip-route` (branch `schem-route`). Never touch other worktrees or
`~/balanced-ternary-logic`. No git commit or push: the integrator reviews and commits.

## Problem

`tritflow.schematic.draw` (used as `net.schematic(...)`) fails on flat netlists produced by RTL synthesis:

    module add2(input trit [1:0] a, b, output trit [2:0] s); assign s = a + b; endmodule
    -> ValueError: No clear schematic channel for 's[0]' at (1024, 960)

    module mul_table(input trit a, b, output reg trit y);
      always @(*) begin case ({a, b}) 2'tTT, 2't11: y = 1't1; 2'tT1, 2't1T: y = 1'tT; default: y = 1't0; endcase end
    endmodule
    -> ValueError: No clear schematic channel for '_n17' at (1120, 1504)

(Synthesize with `tritflow.flow.loads(source).synthesize()`; call `.schematic(net_names=True, expand="*",
title="", legend=False)` and `._repr_svg_()`.) Hand-written hierarchical examples draw fine. The notebook's
chapter 4 needs both of these, and chapter 7 needs `examples/alu.tv` (64 cells) and `examples/adder4_rtl.tv`.

## Goal

Every combinational example under `examples/*.tv` that synthesizes (including RTL ones: `full_add_rtl`,
`adder4_rtl`, `case_table`, `mux_rtl`, `comparator_rtl`, `alu`, `alu9`, and the two sources above) draws
without error and stays readable: no overlapping wires, crossings marked as the renderer already does,
left-to-right logic levels. Prefer a principled fix in placement/routing (more channel room where a net
cannot find a track, adaptive column/row pitch, retry with a wider canvas, track assignment) over special
cases. Keep the existing look (style, symbols, colours, `legend=False`, `inputs=` value colouring and the
`data-net` attributes on wires that the notebook's JavaScript recolours).

## Check

- Tests: existing `tests/` schematic tests keep passing (`python3 -m pytest tests -k schematic -q`); add a test
  that draws every example above. The hand-drawn half/full adder layouts must not change (compare SVGs before
  and after for `examples/half_add.tv`, `full_add.tv`, `adder2.tv`; any difference must be explained).
- Look at the result: render each SVG to PNG (cairosvg or headless Chrome) and look at the images yourself
  after each change; iterate until each is clean. Keep final PNGs under `build/schem-route/`.
- Write `docs/status/SCHEM_ROUTE.md`: the cause, the fix, before/after, the images, what remains.

Rules: TR1UM_PDK=~/pdk/TR-1um-pinned. Edit only `tritflow/schematic/` and `tests/`. Do not change recorded
results or `tritflow/{sim,pnr,extract,cells}`. No new dependencies, no network, no publishing, no sign-in.
