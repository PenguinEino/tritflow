# Figure implementation specifications

This is a handoff to FRONTEND, not notebook prose. Figure anchors in the chapter
files mark insertion points. Every figure has a static initial view and an alt
description. A missing artifact is shown as unavailable with a reason; never
draw a fabricated passing trace or badge. Match numbers to placeholders.md.

## Shared display rules

- Use actual GDS geometry and measured arrays. Suggested logical colors are
  blue/gray/red for −1/0/+1, also identified by text and line style. Keep rail
  colors distinct from logical values. Choose opaque light/dark backgrounds,
  visible grid lines and readable text in both Colab themes.
- Use explicit units on all axes and equal x/y scale for geometry. Put control
  labels above plots. Legends and hover must name the design, output, model
  scope and selected conditions. Display four significant digits, preserve
  full precision for calculations, and do not make sub-timestep speed claims.
- Plotly controls select measured data without a kernel where possible.
  Persist the initial figure plus a static image/table for GitHub renderers
  that do not execute JavaScript. Live HDL editing/rerouting uses the code
  cell and an explicit Run action, with the same static fallback.
- Each chapter has one large composite hero, not a succession of raw report
  dumps. Put native reports, hashes and lengthy conditions under Appendix B.

## Teaser — put the result above the setup

One wide figure, three panels connected by arrows labelled **HDL → cells →
GDS → SPICE**. Left: syntax-highlighted actual `examples/adder.tv`, with the
shared half/full-adder dependencies named below it and the top-level line count
read from that file. Middle (largest panel): actual default-adder routed GDS,
x/y in µm, cell boundaries faint, visible three-supply legend. Right: one
positive and one negative carry event with sum MSB and cout, time in ns,
voltage in V, target bands shaded. Crop from the actual recorded vectors,
not an invented ideal step response. A strip beneath states mapped cells,
die size, drawing-DRC marker count and strict-LVS result from the same design.
No interaction is needed. The entire caption is the two sentences in teaser.md.
Alt: HDL adder linked to its routed cell array and settled analog outputs.

## Chapter 0 — prove the path reaches GDS

Use the teaser's full-size GDS and waveform as a linked composite, with a width
selector for the precomputed N=1…6 records and a visible indication that the
default N=2 is calculated in the current session. Every selector choice must
change GDS, stats, badges, waveform and headline together. Load GDS from the
validated row's native artifacts; no stretching the default image to represent
another width. Disabled/running/failed widths remain listed with their state.
Waveform lanes show inputs, sum bits and cout; label carry assertion/release,
the initialized segment, selected load and input hold. Below: logical checked
vectors and analog states visited/possible as separate counts. Live calculation
uses `flow.load(...).synthesize().place_and_route()` and strict DRC/LVS.
Alt: selected adder layout and carry waveforms with their check results.

## Chapter 1 — connect conduction, logic and DC

Composite: selected primitive schematic and truth table at left; two aligned
transfer panels at right. Axes: input voltage (V) against output voltage (V)
and input voltage (V) against signed rail current (µA). Use
`dc_transfer`/the recorded grid arrays; `sweep_pin` and fixed other-input trit
are in the title. Gate dropdown INV/NAND/NOR/NANY; initial gate NANY, with an
explicit INV selection for the divider prediction. Slider chooses a measured
voltage sample and updates an operating-point marker and numeric readout.
Highlight branch topology only: if no device-current probes were measured,
say “possible conducting path” and never imply measured current density.
For NANY A=−1/B=+1, outline both devices between Y and VMID. In the INV
zero-input view, add a small Ru/Rd equivalent circuit and hand/SPICE comparison
readout. Generate all truth tables with `logic_value`, not image text.
Alt: transistor branches corresponding to the selected truth-table/DC point.

## Chapter 2 — expose the sizing tradeoff

Use `load_grid('INV')`/`load_grid('NANY')` and `sizing_figure` as starting points.
Left: input voltage (V) versus output voltage (V), selected curve bold and
adopted curve dashed. Middle: worst logical level error (mV) versus maximum
absolute rail current (µA); show the whole grid faintly, adopted point as a
star and selected row as an open circle. Error-band threshold is a labelled
horizontal reference if error is the y axis. Right: zero-input hand/SPICE
middle-voltage bars and static-power comparison for INV. Controls select
actual grid dimensions (MOS widths, common MOS length, RR length); label
all W/L in µm. Controls choose a complete existing candidate, never interpolate
between rows as if simulated. Include failed candidates as crosses or a
status strip. Initial selection is adopted dimensions. Alt: changing branch
strength shifts the midpoint and changes current/error across the measured grid.

## Chapter 3 — locate real devices and rail access

Use `cell_figure`, `device_mapping` and `row_abutment`. Top: selected cell
geometry in µm beside its source schematic and a compact device table (original
name, published name, model, W/L). A device dropdown outlines its measured
GDS bounds; initial NANY selection shows the complementary Y–VMID clamp.
Layer toggles include active, gate poly, resistors, M1, V1, M2, boundaries and
pin landings. Bottom strip: a real alternating R0/MY row with all rails named
and free M2 track centerlines dotted. Cell selector includes support cells;
only reference logic cells show original-area/performance comparisons. A
small comparison inset gives reference/adapted area and estimated-metal-C
settling at the same load, with both numeric labels and model scope.
Alt: source-device names mapped to layout plus continuous three-rail abutment.

## Chapter 4 — show how carry preserves the integer sum

Left: actual half/full-adder HDL with selectable matching schematic; avoid
the entire primitive schematic gallery. Right: complete full-adder truth table
with integer total, sum, carry and `sum + 3*carry`. A vector selector highlights
one row and supplies a small digit diagram with radix weights; gates/rows stay
legible at notebook width. Counts come from synthesized examples. Under the
selected row, render the arithmetic identity with the chosen signed digits.
No plot axes; label columns with signal names and signed integer values.
Alt: chosen input digits and their exactly equal sum/carry representation.

## Chapter 5 — recolor the mapped graph

Use `gate_graph`/`color_nets`. Horizontal coordinate is cell stage, vertical
position separates instances; no implication of geometric distance. Gate names
and cell types remain visible; ports have a distinct shape. A vector dropdown
changes net colors and hover pin values using `net_values` without rerunning
synthesis. Use a complete small full-adder input set for static frames; show
the wider adder only if labels remain readable. Include a small source-expression
→ mapped-cell inset for min/NAND+INV and negated-min/NAND. Report cell counts,
depth and equivalence scope for the exact graph being shown.
Alt: value-colored ternary cell network with the source hierarchy in hover.

## Chapter 6 — follow physical connections and supply feeds

Left: `placement_animation` with x/y in µm and a labelled HPWL trace versus
recorded placement step. Right: final `layout_figure`/`render_gds`, with net
and instance selection, M1/M2 layer toggles and visible pin/via markers.
Supply mode colors the drawn power network by estimated rail deviation (mV),
showing actual feed points and branch-current utilization in hover. Selected
signal mode shows its actual conductor and vias. Default is the same adder
as chapter 0. If exposing rows/annealing controls, make rerouting an explicit
live action; retain original and trial geometry separately and relabel every
stat. A seed or more annealing steps is no promise of improvement.
Alt: placement changes and a completed route around real cell obstacles.

## Chapter 7 — make prediction and failure visible

One composite hero with labelled tabs or subpanels, retaining a static overview.

1. **Wiring:** shared time axis in ns, output voltage in V. Solid devices+wire-C
   and dashed identical-device-only traces; ideal levels and ±band shading.
   A transition selector chooses the same segment/output in both runs. Mark
   ramp start and final band entry; annotate their paired difference. The
   prediction is not labelled “pre-layout” when it uses extracted devices.
2. **Load:** load (pF, logarithmic) versus worst settling (ns), with a second
   strip for pass/fail and maximum band error. Slider selects measured loads
   and their corresponding waveform if native arrays are packaged. Annotate
   last-pass/first-fail bracket and hold window. Null delays stay gaps, with
   red failure markers at a labelled status strip, never at zero delay.
3. **Scaling:** width (trits) versus carry-endpoint settling (ns), die area
   (mm²), static power (mW) and rail deviation (mV) in separate aligned panels.
   Device-only/+C points, one-slice hand estimate and OLS fit lines have distinct
   styles. N selector highlights existing measured points and updates the
   headline. Show fitted widths, slopes and residuals without extrapolation.
   Power pane distinguishes zero-state cell-sum prediction, zero-state full
   DC measurement and tested-state maximum. Add branch current utilization
   (%) with the actual reserved-margin threshold, read from PNR assumptions.

Use `waveform_figure`, `load_sweep_figure`, `scaling_figure` and
`scaling_fit_figure` where suitable. Large arrays can stay in the native
artifact archive; summary data alone cannot manufacture a waveform.
Alt: the added wire loading, load pass/fail bracket and width trends compared
with a single-slice delay estimate and a DC cell-power sum.

## Chapter 8 — the edited circuit is the result

Circuit dropdown from `examples.curated.DESIGNS`, followed by the actual
editable HDL code cell. One hero shows generated GDS with µm axes, selected
output waveforms with ns/V axes and bands, and a compact specification/check
strip. Running edited HDL refreshes every panel from `custom_result`;
an oracle disagreement stops before physical work and displays the failing
input/expected/actual row. Static fallback is the unedited minmax example
with the exact displayed source. Alt: edited design, its physical layout and
its independent-reference electrical result.

## Chapter 9 — prepare a matched measurement

A labelled block diagram: three regulated supplies with individual current
measurement → reference-cell chip → high-impedance voltage probe; programmable
input source drives the selected gate, known load connects at the measured
node. Beside it, a table maps DC transfer → level/current, transient → final
band entry, supply/temperature sweep → sensitivity. No fabricated measured
curve, padout or instrument part number. An optional actual chip wrapper may
replace the diagram only with verified current GDS, pad map and clearly
separated geometry-check/approval results; otherwise the diagram is complete.
Alt: measurement signals and records needed to compare silicon with SPICE.

## Appendix A — consolidated scope table

Render the table in A_limits.md with readable wrapping. No interaction or
additional plot is needed. Scope applies to the main results; optional studies
show their own added assumptions alongside their data.

## Appendix B — inspect and repeat the evidence

Generated rows for cell/abutment, each routed design, every width/load point,
regression summary, source/PDK and real-Colab run. Columns identify recorded
versus fresh, pass/fail/unavailable, conditions and a native-report link.
Collapsed tables hold hashes, tools, vectors, Newton guesses and detailed
timings. Include successful and failing/running records. The runtime bar chart
is optional: stage on y, wall time (s) on x, with fresh/reused status in hover.
