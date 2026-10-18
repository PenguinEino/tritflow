# SCHEM status — phase 5 complete

Updated 2026-10-19. Owner paths: `tritflow/schematic/`, `tests/schematic/`,
`docs/status/SCHEM.md`. Public `net.schematic()` / `.annotate()` APIs are unchanged.
No other stream's source was edited; no git state changes or package installs.

## Result and review artifacts

- Before/after PNG review for **all 22 gallery + 4 notebook views**:
  `build/schematic-review/round5/index.html`.
- Frozen phase-4 PNG/SVG/PDF files: `round5/before/{gallery,notebook}/`.
- Final CairoSVG PNGs, each **1000 px wide**, and SVG/PDF originals:
  `round5/after/{gallery,notebook}/`.
- Every gallery metric before/after: `round5/after/gallery/metrics.md`;
  per-net numbers and real-PNR provenance: `manifest.json` beside it.
- Four notebook comparisons: `round5/notebook-metrics.md`.
- Current gallery also published at `build/schematic-review/index.html`.
  Documentation example SVGs and `assets/review_metrics.json` are current.

I opened the phase-4 full_add-flat PNG first. I inspected every final gallery
PNG and all four notebook PNGs, including the actual PNR-capacitance overlays,
at 1000 px wide. Final inspection found no remaining port loops beyond the
sheet edge, inconsistent module interiors, cramped labels, text collisions,
short pin-entry jogs or wires on symbol edges. The 20 circuit SVGs were also
regenerated from the final source and matched the inspected files exactly.

## Implementation and decisions

`macros.py` obtains the same standalone half_add / mul1 layout used by the
public renderer, then copies cell positions, orientations, pin coordinates
and internal-net routes into each frame. There is no second folded half-adder
placement. Exact ordered-pin grammars identify modules, independent of cell
instance names; missing serialized child scopes can be recovered from the
verified full-adder grammar. Original instance names and terminals remain in
the connection ledger; framed gate labels use the canonical circuit roles.

Standalone port flags become explicit named frame pins. Short, fixed boundary
adapters separate half-adder a/b terminals; mul1 operands enter at opposite
ends of their existing fan-out trunks. These adapters affect port nets only.
Carry leaves above its actual producer, and sum leaves at right. Parent A*
routing treats each entire frame as a solid keep-out. Its separate
`scene.interconnect` geometry and frame pin maps are serialized and audited;
a parent wire cannot enter a frame interior.

Full_add-flat keeps ha1/ha2 side by side, a/b directly left of ha1, cin in the
gap, sum directly right of ha2, and the carry-combining gates and cout above
ha2 in a dedicated channel. The **3.66:1** full canvas deliberately replaces
the old folded **2.17:1** arrangement: the latest instruction to reuse the
clean standalone module takes precedence over folding its gates to reach 2:1.
Flat adder2/adder4 use one digit per row so 9 pt labels remain readable at
1000 px; hierarchical ripple adders retain the straight cout→cin chain.

Mul2 keeps four identical mul1 frames in a 2×2 product matrix, with the two
identical half-adders at right. Its shared b[1] flag sits above the second
column. MAC's exact four-cell multiplier cone is framed too; its two exported
Boolean taps have t1/t3 boundary pins and separate buffer rows. Compare2's
seven dependency columns now stay feedforward: no final-stage return to the
left edge, and crossings fall from 3 to 0.

All text has a **9 pt minimum when displayed at 1000 px wide**, including
frame labels, formal pin names, gate names, footnotes and overlays. Text size
in SVG pixels is converted with `size × 0.75 × 1000 / canvas_width` for the
independent test. Gate name strips and larger flags reserve space for it;
actual text bounds are checked against every wire, foreign symbol and label.
Names may extend a few pixels into their own empty side halo, above the gate
outline, without moving the gate or changing the shared template. Symbol
strokes have a 0.8 display-pixel minimum. NAND/NOR use their familiar outlines;
minimum/maximum are explained in the legend instead of cramped body text.
The serif family and trit palette continue to match `figures/style.py`.

One primary fan-out trunk is required **per routing domain**: each reusable
module retains its local operand trunk, while the parent gets one bus between
frame boundary pins. Different-net parallel wires still need 32 px spacing;
primary trunks need 48 px; foreign pins/dots/outlines need 16 px clearance;
each pin keeps a straight 32 px approach. All counters remain zero. This
scoped rule is necessary for identical module reuse; the same electrical net
can have a local bus in several instances and one parent bus.

Real-C demos still call **PnrResult.net_parasitics()** on actual library routes
(`library_mock=false`); they use `wire_capacitance_f`, not pin C or synthetic
values. The gallery half-adder has nine reported nets, with total estimated
wire C of 447.7378164 fF. Notebook annotated uses the real adder2 PNR result. Overlays
reuse the exact scene; plain diagrams have no empty net-name legend.

## Visual loop and defects resolved

- Original / pass 1: confirmed the different folded half-adder placement and
  a/b sheet-edge loops. Replaced them with standalone templates and boundary
  routing. Found faint strokes, undersized flags and missing MAC tap ports.
- Passes 2–3: enlarged flags/type, reserved pin access while placing flags,
  separated MAC buffers, and fixed too-close entry leads beside operand
  trunks. Parent wires were confined to frame channels.
- Passes 4–5 (all 26 PNGs): found compare2's returning lower row and unnecessary
  multiplier entry bends. Kept compare2 feedforward and moved mul1 entries to
  its existing trunks. Preserved mul2's 2×2 matrix and put its halves at right.
- Pass 6: an experimental wider gate keep-out caused half-adder carry detours;
  the clearance audit and direct image inspection caught this. Restored the
  clean standalone half geometry; handled readable labels in the name strip
  and flags instead. Fixed a shared-input/output flag stub conflict in mul2.
- Pass 7 / final `after/`: inspected all 22 gallery and 4 notebook PNGs. Fixed
  the last large-font C-footnote clipping case. No remaining visual defects
  observed; all independent clearance/type/connectivity checks pass.

## Objective metrics — phase 4 → phase 5

Length is unique drawing-wire length, not chip micrometres. Bends are unique
same-net degree-two corners, excluding T joins. Counts include both module
interiors and parent interconnect; aspect includes overlay tables.

The full-adder templates reduce bends **38→30** (max/net **7→5**), and flat
adder2/adder4 reduce bends **78→64 / 158→132**. Blocked interiors cost longer
parent routes: MAC/mul2 flat wire rises **12672→17696 / 20904→29152**, and their
crossings rise **12→16 / 15→26**. All crossings have gaps and stay clear of
pins/dots. These costs are reported rather than hidden by moving gates away
from their standalone templates. Original wire/bend budgets remain; the
additional comparison budget now uses the immediately reviewed phase-4
baseline, with explicit bounds for frame-channel costs.

| Figure | Wire px | Bends total | Bends/net mean | Bends/net max | Crossings | Aspect | Min font pt @1000px |
|---|---:|---:|---:|---:|---:|---:|---:|
| half_add-hierarchical | 3776 → 3648 | 8 → 8 | 0.89 → 0.89 | 2 → 2 | 5 → 5 | 2.66 → 2.54 | 4.7 → 9.0 |
| half_add-flat | 3776 → 3648 | 8 → 8 | 0.89 → 0.89 | 2 → 2 | 5 → 5 | 2.66 → 2.54 | 4.7 → 9.0 |
| full_add-hierarchical | 1360 → 1344 | 6 → 8 | 0.67 → 0.89 | 4 → 4 | 0 → 0 | 4.24 → 4.48 | 6.0 → 9.0 |
| full_add-flat | 9792 → 11072 | 38 → 30 | 2.00 → 1.58 | 7 → 5 | 11 → 12 | 2.17 → 3.66 | 3.4 → 9.0 |
| adder2-hierarchical | 496 → 512 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.51 → 1.58 | 10.5 → 10.0 |
| adder2-flat | 21704 → 24768 | 78 → 64 | 2.11 → 1.73 | 7 → 7 | 24 → 29 | 1.11 → 1.83 | 3.3 → 9.0 |
| adder4-hierarchical | 944 → 960 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 2.57 → 2.64 | 6.2 → 9.0 |
| adder4-flat | 46360 → 52224 | 158 → 132 | 2.16 → 1.81 | 7 → 7 | 62 → 63 | 2.26 → 0.90 | 1.6 → 9.0 |
| mul1-hierarchical | 1856 → 1808 | 8 → 8 | 1.33 → 1.33 | 2 → 2 | 2 → 2 | 2.84 → 2.64 | 6.9 → 9.0 |
| mul1-flat | 1856 → 1808 | 8 → 8 | 1.33 → 1.33 | 2 → 2 | 2 → 2 | 2.84 → 2.64 | 6.9 → 9.0 |
| mac1-hierarchical | 3488 → 3224 | 10 → 12 | 0.77 → 0.92 | 3 → 3 | 2 → 2 | 3.27 → 3.09 | 4.3 → 9.0 |
| mac1-flat | 12672 → 17696 | 46 → 56 | 1.70 → 2.07 | 7 → 8 | 12 → 16 | 3.18 → 2.14 | 2.1 → 9.0 |
| sign-hierarchical | 592 → 592 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 1.40 → 1.45 | 14.1 → 12.4 |
| sign-flat | 592 → 592 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 1.40 → 1.45 | 14.1 → 12.4 |
| compare2-hierarchical | 4224 → 2728 | 10 → 8 | 0.71 → 0.57 | 4 → 4 | 3 → 0 | 1.58 → 3.69 | 6.6 → 9.0 |
| compare2-flat | 4224 → 2728 | 10 → 8 | 0.71 → 0.57 | 4 → 4 | 3 → 0 | 1.58 → 3.69 | 6.6 → 9.0 |
| mul2-hierarchical | 5728 → 5648 | 24 → 24 | 2.00 → 2.00 | 4 → 4 | 7 → 7 | 2.52 → 2.55 | 4.3 → 9.0 |
| mul2-flat | 20904 → 29152 | 73 → 76 | 2.15 → 2.24 | 7 → 9 | 15 → 26 | 1.38 → 2.29 | 2.7 → 9.0 |
| minmax-hierarchical | 1360 → 1328 | 4 → 4 | 0.67 → 0.67 | 2 → 2 | 2 → 2 | 2.09 → 1.96 | 9.4 → 9.2 |
| minmax-flat | 1360 → 1328 | 4 → 4 | 0.67 → 0.67 | 2 → 2 | 2 → 2 | 2.09 → 1.96 | 9.4 → 9.2 |
| half_add-overlay | 3776 → 3648 | 8 → 8 | 0.89 → 0.89 | 2 → 2 | 5 → 5 | 2.35 → 2.14 | 4.7 → 9.0 |
| legend | 0 → 0 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.74 → 1.74 | 6.9 → 9.0 |


### Notebook views

| Figure | Wire px | Bends total | Bends/net mean | Bends/net max | Crossings | Aspect | Min font pt @1000px |
|---|---:|---:|---:|---:|---:|---:|---:|
| half | 3776 → 3648 | 8 → 8 | 0.89 → 0.89 | 2 → 2 | 5 → 5 | 2.43 → 2.23 | 4.7 → 9.0 |
| minmax | 1360 → 1328 | 4 → 4 | 0.67 → 0.67 | 2 → 2 | 2 → 2 | 2.09 → 1.96 | 9.4 → 9.2 |
| adder2 | 496 → 512 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.25 → 1.31 | 10.5 → 10.0 |
| annotated | 496 → 512 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.21 → 1.26 | 10.5 → 10.0 |


Across all final gallery and notebook scenes: **0 short jogs, 0 rotated gates,
0 symbol-edge runs, 0 clearance violations, 0 parent-frame intrusions**.
Every displayed label meets the 9 pt minimum; all figures include exact
terminal accounting and connected same-net geometry.

## Validation and reproduction

`python3 -m pytest tests/schematic -q` → **170 passed in 37.05 s**.
This retains the prior 135 tests and adds 35 cases for exact standalone macro
reuse, fixed internal routes, boundary-channel isolation, local flags,
1000 px type size, one digit per row, feedforward compare2, hierarchy recovery,
selective expansion, frame-contained templates and unused-input preservation.
SVG/PDF/PNG, deterministic ordering, every terminal, real PNR integration,
all-overlay text bounds and the phase-4 spacing rules remain covered.
`git diff --check` on the owned paths is clean.

Reproduce the complete gallery and notebook PNGs:

```bash
python3 -m tritflow.schematic.review --output build/schematic-review/round5/after
```

CairoSVG is an already installed review-only dependency. Runtime SVG remains
standard-library Python; PDF/PNG use the existing Matplotlib dependency.
No packages were installed. Phase-4 geometry/type baseline is frozen in
`tritflow/schematic/assets/phase4_metrics.json`; original/phase-2/phase-3
baselines and the round-4 artifacts remain available for historical review.

## In progress / blockers / interface requests

None. Phase 5 is complete. FRONTEND's existing schematic delegate and notebook
calls pick up these improvements without any API or notebook changes.
