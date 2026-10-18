# SCHEM status — phase 4 complete

2026-10-19. Implemented the requested drawing rules without changing the
`net.schematic()` / `.annotate()` API. **135 tests pass**. Opened the four
integrator PNGs before editing, then rendered and personally inspected all
22 gallery figures plus all four notebook views through CairoSVG. Final
remaining defects from the requested review: **none observed**.

## Done

- Parallel wires from different nets have **32 px** separation. Pin stubs,
  symbol/label keep-outs and branch dots have at least **16 px** foreign-wire
  clearance. Dot routing uses a more conservative 24 px centre separation.
  Orthogonal crossings remain explicit gaps, away from pins and dots.
- Every fanout net gets one explicit rail, with **48 px** between parallel
  rails of different nets. Operand buses follow a deterministic order. Local
  loads tap their rail; output flags/external module consumers can branch at
  the producer. This removes the ambiguous close a/b ladders in half/minmax.
- Every pin gets a protected **32 px straight approach**, without turns or
  branches inside it. The router retains the pin direction at the escape tip;
  this also eliminates short stairs immediately after an otherwise legal stub.
  No short jogs, rotated gates or symbol-edge runs remain in any final view.
- The inverter-output and carry channels in the half adder are separated from
  neighbouring pins. Its t trunk stays straight and every net remains within
  **2 bends**. Minmax now also has a **2-bend maximum**.
- Legends appear only with settled values or wire C, and contain **port nets
  only**. `net_names=True` alone creates no empty legend. Internal SVG hover
  captions use the producing gate/module terminal, such as `g_t.Y`; exact
  logical names remain in metadata and `data-net`. Unknown anonymous block
  pins get readable `in 1` / `out 1` labels; supplied formal names are retained.
- Separate graphical branch/crossing keys replace the whitespace-dependent
  footnote. The header is **48 px**, side margins **24 px**, title **12 px**.
  Placement's unused routing workspace is cropped away. Fonts, colours and
  symbol strokes retain the paper style.
- Full-adder halves remain side by side; the carry stage occupies the middle
  of each panel and lower rails sit inside its light frame. Full-add flat
  aspect is **2.17:1**. Multirow adders leave enough space for the next row's
  operand flags to sit outside the preceding frame.
- Mul2 flat uses a **2×2 partial-product matrix**, with accumulating halves at
  right. Crossings fall **21 → 15** against phase 3 (36 in the intermediate
  round-4 layout). The hierarchical low-product flag sits above its producer,
  preserving the operand-bus channel between multiplier blocks.

## Visual loop and resolved defects

| Review | Images inspected | Remaining defects found | Resolution |
|---|---:|---|---|
| Supplied notebook PNGs | 4 | Operand ladders only 8 px apart; nearby pins/dots; name-only legend and anonymous carry; collapsed footnote; large top margin/title | Added real wire/pin clearances, port-only overlays, graphical key and crop |
| pass1 | 22 + 4 | Minmax/sign lead-in hooks; unused short spurs in several views; lower-stage spacing | Explicit rails, source-aware routing, terminal-aware spur trimming and larger local channels |
| pass2 | 22 + 4 | Carry rails outside frame; pin-tip short stairs found by tests; mul2 wrapped operand buses | Frame margin, initial pin-direction tracking, 2×2 product matrix |
| final after, including row-gap correction | 22 + 4 | A next-row operand flag initially sat inside the preceding flat-adder frame | Increased row spacing and added a port/frame ownership regression check; rerendered and reinspected |
| Final remaining defects | 26 | **None observed** | Every geometry counter is zero; labels checked against wires, symbols and other labels |

The supplied notebook PNGs are preserved unchanged in
`build/schematic-review/round4/before/notebook/`. Gallery before PNGs come
from the saved phase-3 SVGs through CairoSVG. Final PNGs come from final SVGs
at scale 1.25; this catches browser whitespace/layout behaviour that the
Matplotlib-only previews missed. Intermediate successful reviews are retained
under `pass1/` and `pass2/`. The final set is `after/{gallery,notebook}/`.

## Objective validation and decisions

- `audit.py` independently checks parallel spacing, trunk spacing, foreign
  pin-stub clearance, pin turns and full approaches, symbol clearance, branch
  dot clearance, and exactly one rail for each fanout net. All eight counters
  are **zero** for every final gallery and notebook schematic. Tests also
  reject dangling wire tails and ports inside unrelated hierarchy frames.
- Renderer font measurements check labels against routed wires, other symbols
  and other labels. Tests retain exact terminal accounting, electrical
  connectivity, no wire-through-symbol, no shared different-net edges,
  deterministic ordering, hierarchy expansion, formal aliases and exports.
- The old short-wire budgets assumed 8 px parallel channels. Their bounds
  were revised explicitly for the new 32/48/16 px rules; the original 101
  test cases remain, with 34 additional cases. Tests retain bounds against the
  original gallery, a near-2:1 full-add flat panel and the half-add bend target.
  Tight spacing is no longer rewarded as a shorter wire metric.
- The cost is visible in the tables: half-add wire length **2,200 → 3,776 px**;
  adder4-flat **23,856 → 46,360 px**, crossings **32 → 62**. Those crossings
  have clear gaps and full feature separation. Mul2's matrix removes needless
  wrapping, reducing its flat crossings **21 → 15**. No aggregate hides these
  tradeoffs. Aspect now reflects compact margins rather than artificial blank
  top/bottom space (notably the wide two-block full-add hierarchy).
- The new phase-3 fixture includes before clearance counts. They were computed
  by rebuilding the saved phase-3 placement/routing; each rebuilt wire length
  matches its frozen metric exactly. Old notebook canvas aspects match the
  supplied screenshot dimensions within raster rounding. Geometry comparisons
  do not compare physical C values between independent selected routes.
- Both overlays use **real cell-library PNR** and public
  `PnrResult.net_parasitics()`, reading `wire_capacitance_f`. The half-add's
  nine logical nets still total **447.7378164 fF**; its legend shows only the
  four port nets. The notebook's annotated adder uses its own real PNR report.
  No synthetic capacitance, new DRC/LVS claim, package install, shared source
  edit or git-state change was introduced.

## Review artifacts

[All 26 before/after PNG pairs](../../build/schematic-review/round4/index.html) ·
[Final gallery](../../build/schematic-review/round4/after/gallery/index.html) ·
[Every-gallery metrics](../../build/schematic-review/round4/after/gallery/metrics.md) ·
[Notebook metrics](../../build/schematic-review/round4/notebook-metrics.md) ·
[API and rendering guide](../../tritflow/schematic/README.md)

Committed review data/figures:
[current per-net metrics](../../tritflow/schematic/assets/review_metrics.json),
[phase-3 baseline](../../tritflow/schematic/assets/phase3_metrics.json),
[full-add flat](../../tritflow/schematic/assets/full_add-flat.svg),
[full-add hierarchy](../../tritflow/schematic/assets/full_add.svg),
[adder4 hierarchy](../../tritflow/schematic/assets/adder4.svg),
[legend](../../tritflow/schematic/assets/legend.svg).
The established `build/schematic-review/index.html` also has the final gallery.

## Every gallery item: phase 3 → phase 4

Wire length is in drawing pixels, not chip micrometres. A bend is a unique same-net degree-two orthogonal corner; T joins are excluded. Crossings count distinct different-net perpendicular intersections. Aspect is full canvas width / height; the real-C overlay includes its annotation table.

| Figure | Wire px | Bends total | Bends/net mean | Bends/net max | Crossings | Aspect |
|---|---:|---:|---:|---:|---:|---:|
| half_add-hierarchical | 2200 → 3776 | 9 → 8 | 1.00 → 0.89 | 2 → 2 | 5 → 5 | 1.68 → 2.66 |
| half_add-flat | 2200 → 3776 | 9 → 8 | 1.00 → 0.89 | 2 → 2 | 5 → 5 | 1.68 → 2.66 |
| full_add-hierarchical | 1072 → 1360 | 8 → 6 | 0.89 → 0.67 | 4 → 4 | 0 → 0 | 1.85 → 4.24 |
| full_add-flat | 5040 → 9792 | 31 → 38 | 1.63 → 2.00 | 6 → 7 | 8 → 11 | 2.15 → 2.17 |
| adder2-hierarchical | 448 → 496 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.28 → 1.51 |
| adder2-flat | 11152 → 21704 | 69 → 78 | 1.86 → 2.11 | 8 → 7 | 16 → 24 | 1.13 → 1.11 |
| adder4-hierarchical | 864 → 944 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 2.12 → 2.57 |
| adder4-flat | 23856 → 46360 | 137 → 158 | 1.88 → 2.16 | 8 → 7 | 32 → 62 | 2.16 → 2.26 |
| mul1-hierarchical | 1152 → 1856 | 9 → 8 | 1.50 → 1.33 | 3 → 2 | 2 → 2 | 1.67 → 2.84 |
| mul1-flat | 1152 → 1856 | 9 → 8 | 1.50 → 1.33 | 3 → 2 | 2 → 2 | 1.67 → 2.84 |
| mac1-hierarchical | 2176 → 3488 | 12 → 10 | 0.92 → 0.77 | 3 → 3 | 3 → 2 | 2.32 → 3.27 |
| mac1-flat | 6920 → 12672 | 42 → 46 | 1.56 → 1.70 | 6 → 7 | 10 → 12 | 2.72 → 3.18 |
| sign-hierarchical | 312 → 592 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 0.83 → 1.40 |
| sign-flat | 312 → 592 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 0.83 → 1.40 |
| compare2-hierarchical | 3048 → 4224 | 9 → 10 | 0.64 → 0.71 | 4 → 4 | 3 → 3 | 1.27 → 1.58 |
| compare2-flat | 3048 → 4224 | 9 → 10 | 0.64 → 0.71 | 4 → 4 | 3 → 3 | 1.27 → 1.58 |
| mul2-hierarchical | 2848 → 5728 | 23 → 24 | 1.92 → 2.00 | 3 → 4 | 7 → 7 | 1.74 → 2.52 |
| mul2-flat | 14032 → 20904 | 71 → 73 | 2.09 → 2.15 | 7 → 7 | 21 → 15 | 1.47 → 1.38 |
| minmax-hierarchical | 768 → 1360 | 5 → 4 | 0.83 → 0.67 | 3 → 2 | 2 → 2 | 1.23 → 2.09 |
| minmax-flat | 768 → 1360 | 5 → 4 | 0.83 → 0.67 | 3 → 2 | 2 → 2 | 1.23 → 2.09 |
| half_add-overlay | 2200 → 3776 | 9 → 8 | 1.00 → 0.89 | 2 → 2 | 5 → 5 | 1.44 → 2.35 |
| legend | 0 → 0 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.74 → 1.74 |

A short jog is a leg shorter than one gate input pitch (32 px) between two degree-two corners. Terminal stubs and T joins are excluded; pin access uses the finer 8 px raster. Edge runs count positive overlap along any symbol/label keep-out boundary; perpendicular pin contact is allowed.

| Figure | Short jogs | Rotated gates | Symbol-edge runs | Clearance violations |
|---|---:|---:|---:|---:|
| half_add-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 27 → 0 |
| half_add-flat | 0 → 0 | 0 → 0 | 0 → 0 | 27 → 0 |
| full_add-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 16 → 0 |
| full_add-flat | 0 → 0 | 0 → 0 | 0 → 0 | 93 → 0 |
| adder2-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| adder2-flat | 0 → 0 | 0 → 0 | 0 → 0 | 195 → 0 |
| adder4-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |
| adder4-flat | 0 → 0 | 0 → 0 | 0 → 0 | 381 → 0 |
| mul1-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 26 → 0 |
| mul1-flat | 0 → 0 | 0 → 0 | 0 → 0 | 26 → 0 |
| mac1-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 37 → 0 |
| mac1-flat | 0 → 0 | 0 → 0 | 0 → 0 | 124 → 0 |
| sign-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 4 → 0 |
| sign-flat | 0 → 0 | 0 → 0 | 0 → 0 | 4 → 0 |
| compare2-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 23 → 0 |
| compare2-flat | 0 → 0 | 0 → 0 | 0 → 0 | 23 → 0 |
| mul2-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 72 → 0 |
| mul2-flat | 0 → 0 | 0 → 0 | 0 → 0 | 206 → 0 |
| minmax-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 | 18 → 0 |
| minmax-flat | 0 → 0 | 0 → 0 | 0 → 0 | 18 → 0 |
| half_add-overlay | 0 → 0 | 0 → 0 | 0 → 0 | 27 → 0 |
| legend | 0 → 0 | 0 → 0 | 0 → 0 | 0 → 0 |

## Four notebook views: phase 3 → phase 4

Before geometry uses the saved phase-3 drawing and renderer; its canvas aspect matches each supplied screenshot. After uses the public notebook calls. Drawing pixels are independent of PNG export scale. Wire C is real PNR in the after image; this table compares drawing geometry only.

| Figure | Wire px | Bends total | Bends/net mean | Bends/net max | Crossings | Aspect |
|---|---:|---:|---:|---:|---:|---:|
| half | 2200 → 3776 | 9 → 8 | 1.00 → 0.89 | 2 → 2 | 5 → 5 | 1.44 → 2.43 |
| minmax | 768 → 1360 | 5 → 4 | 0.83 → 0.67 | 3 → 2 | 2 → 2 | 1.02 → 2.09 |
| adder2 | 448 → 496 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.02 → 1.25 |
| annotated | 448 → 496 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.02 → 1.21 |

All four after views have zero short jogs, rotated gates, symbol-edge runs and clearance violations.

## Tests and regeneration

```bash
python3 -m pytest tests/schematic -q
# 135 passed in the final run, including real cell-library PNR integration.
python3 -m compileall -q tritflow/schematic
python3 -m tritflow.schematic.review --output build/schematic-review/round4/after
```

The review helper enforces zero clearance/jog violations before accepting a
review set. CairoSVG was already installed; it is a review-only dependency.
Production native SVG and vector PDF APIs have no new dependency. Fresh-process
SVG and PDF hashes agree at PYTHONHASHSEED=1,42,123 for half_add, full_add-flat,
adder4-flat and mul2-flat. Reversed netlist/port ordering is also tested.

## Interface requests / in progress / blockers

No phase-4 interface request or blocker. The existing FRONTEND delegate and
notebook calls use the improved renderer automatically. Optional source module
port metadata for arbitrary authored modules remains supported by `hierarchy=`;
verified arithmetic already has formal aliases. All requested SCHEM work and
final visual inspection are complete.
