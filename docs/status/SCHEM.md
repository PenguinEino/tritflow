# SCHEM status

2026-10-18 — **complete within SCHEM ownership**. The public drawing hook,
render/export stages, hierarchy controls, overlays, documentation and regression
checks are implemented. No blockers and no new Python/system packages installed.
No shared/other-stream source paths or git state were changed by SCHEM.

## Delivered

- `tritflow.schematic.draw(netlist, ...)` → `Schematic` with SVG text, vector PDF
  bytes, `.show()`, native notebook SVG representation, `.save()` and PNG preview.
- Textbook INV/BUF triangles, NAND/−min and NOR/−max outlines, a distinct clipped
  summing NANY/−sat(a+b) body, supply-style +1/0/−1 sources and directional ports.
  The bubble means ternary arithmetic sign reversal. The one-figure symbol
  legend and shape rationale are in
  [the package guide](../../tritflow/schematic/README.md), with a committed
  [SVG legend](../../tritflow/schematic/assets/legend.svg).
- Deterministic longest-path columns, barycenter crossing reduction, numerical
  bit ordering, reserved long-net lanes, orthogonal channel wiring, merged
  same-net trunks, proper branch dots and gaps at unconnected crossings.
- Default module-instance blocks, `expand='*'` / `'all'` flat views and selective
  path expansion. Unary generate-only scopes compress to `digit[i].fa`.
- Immutable overlay views (`.annotate(...)`) sharing the exact same scene:
  settled trit colours from `figures/style.py`, net names and wire C labels in
  fF. Larger C increases line width and darkness. Every original cell terminal
  and external port occurs exactly once in the SVG metadata connection ledger.
- SVG writer uses only the standard library. PDF/PNG lazily use the project's
  existing Matplotlib dependency, with the same symbol paths and coordinates.
  No Graphviz, Cairo, Xschem, TeX, browser or new dependency.

## Decisions and limits

1. The public mapped netlist retains hierarchy paths but not source module
   types or module port aliases. Block labels therefore show instance paths,
   cell counts and actual boundary net names. No guessed a/b/sum aliases and
   no dependency on the source parser. All original internal terminals remain
   in the block's connection ledger; they become visible pins when expanded.
2. Optimized sharing can make a scope electrically non-convex. Closing such a
   block would imply a false feedback loop. The affected scopes automatically
   open; `scene.notes` records the decision. A dedicated regression covers it.
3. Complete flat ripple adders are wide. SVG preserves native-size labels and
   every connection, and the review index supports horizontal scrolling.
   Hierarchical views are the default overview; no gates are dropped to fit.
4. Values mean settled ideal −1/0/+1, not analog voltages or transient states.
   C means PNR's estimated routed wire C, not pin C, total load or signoff PEX.
5. Labels have reserved channel space, so adding/removing annotations never
   changes geometry. Bus bits are ordered in ascending numerical order.

## PNR integration — implemented and verified

PNR's `PnrResult.net_parasitics()` landed during implementation. The adapter
calls that public method and reads `report['nets'][net]['wire_capacitance_f']`.
It also accepts `{net: farads}` and extraction-style `capacitance_f` records.
It never substitutes receiving-pin capacitance or `total_load_f` for wire C.
Exact logical-name matching preserves case and vector indices. Global rails
outside the logical netlist are ignored; invalid/negative/nonfinite C is an
error.

The automated integration test runs the public PNR flow with its explicit
metal-only mock library in a temporary directory, then consumes the real
`PnrResult.net_parasitics()` method. This tests the actual published report
schema and method, without requiring physical signoff tools.

Separately consumed the retained **real-library** `build/full_add/full_add.json`
and embedded report in `build/full_add/full_add.pnr.json`: all 19 logical nets
matched, with total routed wire C **1311.297252 fF**. The result's JSON path was
redirected to SCHEM's review directory, so calling the public method wrote only
SCHEM's sidecar, leaving PNR's original artifacts alone. Inspected the resulting
[full-adder C/value overlay](../../build/schematic-review/physical/full_add-pnr-overlay.png).
This is an interface/visualization check of the existing PNR result, not a new
DRC/LVS qualification claim.

## Visual review

Generated and personally inspected **all 22 PNGs**: hierarchical and flat
half_add, full_add, adder N=2 and N=4, mul1, mac1, sign, compare2, mul2 and
minmax; plus the legend and an explicitly synthetic C/value overlay. Also
inspected the real-PNR full-adder overlay and native-resolution left/middle/right
crops of the flat full adder.

Review iterations corrected the gate-body/pin alignment, removed unnecessary
8-pixel steps when a driver pin row is free, and retained visible crossing gaps
and branch dots. Font-metric checks find zero overlapping labels or clipped
labels in all 20 circuit views with every overlay enabled. Geometry checks find
zero overlapping symbols, zero wire-through-symbol/label keep-outs, zero
same-direction shared metal between different nets, and no disconnected net
pieces.

[Review index (SVG/PDF/PNG)](../../build/schematic-review/index.html) ·
[Manifest](../../build/schematic-review/manifest.json) ·
[Committed full-adder overview](../../tritflow/schematic/assets/full_add.svg) ·
[Committed flat full adder](../../tritflow/schematic/assets/full_add-flat.svg)

The generated review set lives under ignored `build/` and can be reproduced:

```bash
python3 -m tritflow.schematic.gallery --output build/schematic-review
```

## Interface requests — FRONTEND handoff

Only FRONTEND/integrator-owned glue remains, as explicitly required by the brief.
Add this delegate **once in `tritflow.synth.mapping.SynthesizedNetlist`** so the
public `flow.Netlist` subclass inherits it and direct synthesis also exposes it:

```python
def schematic(self, **options):
    from tritflow.schematic import draw
    return draw(self, **options)
```

Notebook, between synthesis and P&R:

```python
sch = net.schematic()
display(sch)
# Optional controls can reuse this exact scene:
# display(sch.annotate(inputs={...}, net_names=True))
# display(sch.annotate(parasitics=lay.result))
# display(net.schematic(expand='*'))
```

Until the delegate lands, `draw(net)` is fully functional and uses only public
GateNetlist/evaluator/PNR APIs. No monkey-patching or shared-file edits.

## Verification

```bash
python3 -m pytest tests/schematic -q
# 53 passed; includes live PNR-method integration, all requested examples in
# both views, selective hierarchy, non-convex sharing, constants, repeated pins,
# unused inputs, bit ordering, label metrics, electrical connectivity, exact
# terminal accounting, invalid inputs, XML escaping, palette and SVG/PDF/PNG.
python3 -m compileall -q tritflow/schematic
```

SVG and PDF were also byte-identical across three fresh Python processes with
`PYTHONHASHSEED=1`, `42` and `123`. No timestamp or ambient hash-order dependency.
`git diff --check` reports no whitespace errors in the owned paths.
