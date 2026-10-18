# SCHEM status — phase 6 complete

Updated 2026-10-19. Owner paths: `tritflow/schematic/`, `tests/schematic/`,
`docs/status/SCHEM.md`. Public `net.schematic()` / `.annotate()` calls are
unchanged. SCHEM did not edit `notebook/` or other streams' source, change git
state, or install packages. No blockers or new interface requests.

## Result and review evidence

Read COLAB's round-9 “Schematic and figure readability” feedback and opened
all six requested screenshots before editing: `round9-07`, `08a/b/c`, `11a`
and `12`. The important missed distinction was the SVG's intrinsic width:
a prior 1000 px review PNG hid the flat half-adder's actual 1440 px export.

All four notebook schematics now fit a **1000×700 px envelope**, both at their
natural size and in the requested 1000 px PNG review. Every notebook label,
including gate IDs, branch/crossing keys, port values and wire-C numbers/units,
is at least **11 pt** in both modes. All final PNGs were opened and inspected;
no remaining overlaps, clipping or scroll-sized notebook exports were found.
This is local SVG/CairoSVG/Matplotlib verification against real-Colab feedback,
not a new live Colab run.

- [Before/after visual review](../../build/schematic-review/round6/index.html):
  unresized PNGs inside a fixed 1000×700 px pane and separate 1000 px previews.
- [Notebook dimensions and routing metrics](../../build/schematic-review/round6/notebook-metrics.md).
- [All 22 gallery figures](../../build/schematic-review/round6/after/gallery/index.html)
  and [all before/after metrics](../../build/schematic-review/round6/after/gallery/metrics.md).
- Frozen inputs: `build/schematic-review/round6/before/{gallery,notebook}/`.
  Final SVG/PDF/PNG files: `round6/after/{gallery,notebook}/`.
  Notebook `*-native.png` files have **no raster resize**.
- The root `build/schematic-review/index.html` and documentation SVGs are current.
  Previous phase-5 notes are frozen in `round6/source-before/SCHEM.md`;
  phase-5 visual evidence remains under `build/schematic-review/round5/`.

## Before / after sizes

Dimensions below are px, rounded to whole pixels; the half-adder's precise
natural height is 460.294. The adder drawing itself shrinks **672→640 px**;
its new 208 px side key replaces the bottom key, explaining the wider but
shorter total export. The plain flat half-adder is **1000×394 px**. All four
half-adder overlay combinations (plain, values, C, both) stay within the bound.

| View | Natural px before → after | PNG @1000 px before → after | Min font pt native before → after | Min font pt @1000 before → after |
|---|---:|---:|---:|---:|
| half | 1440×646 → 1000×460 | 1000×449 → 1000×460 | 12.96 → 11.00 | 9.00 → 11.00 |
| adder2 | 672×514 → 848×424 | 1000×765 → 1000×500 | 6.75 → 11.00 | 10.04 → 12.97 |
| annotated | 672×532 → 848×424 | 1000×792 → 1000×500 | 6.75 → 11.00 | 10.04 → 12.97 |
| minmax | 736×376 → 736×376 | 1000×511 → 1000×511 | 6.75 → 11.00 | 9.17 → 14.95 |

## Implementation and decisions

- `placement.py`: tighten the shared half-adder column pitch **192→176 px**
  and move the sign-reversal branch above the sum row. Keep u→c and t→d
  straight. Framed half-adders still reuse this exact standalone template.
  Tighten the hierarchical ripple digit pitch **224→192 px**, preserving the
  straight cout→cin chain. Reserve flag width for the larger displayed type.
- `routing.py`: permit half-pitch candidate adjustments before wider fan-out
  rail searches. The actual clearance constraints remain unchanged: 32 px
  parallel-net spacing/straight pin access, 48 px fan-out-trunk spacing, and
  16 px foreign-pin/dot/outline clearance. The half-adder now has wire length
  **3648→3104**, crossings **5→2**, and still at most two bends per net.
- `vector.py`: cap intrinsic SVG/PDF/PNG export width at 1000 px while keeping
  routing coordinates in the viewBox. Scale Matplotlib text/strokes with the
  same factor. Resizing only a PNG preview would not fix actual Colab output.
- `render.py` / `legend.py`: use at least 11 pt at native size; scenes with up
  to ten visible gates/blocks also meet 11 pt at 1000 px. All text roles share
  this floor, including gate IDs and C units. Large expanded galleries retain
  their established 9 pt floor at 1000 px. Put notebook adder keys in the
  available right column and wrap the C explanation into two readable lines.
- Larger type exposed a compare2 output-flag collision and a mul2 hierarchical
  module-caption collision. Widen flags before routing and increase caption
  leading; both are covered by the existing independent text audit.
- `Schematic.metrics` adds `rendered_width_px`, `rendered_height_px` and
  `min_font_pt_native`. Existing width/height continue to describe the logical
  viewBox, so geometry metrics and exact annotation-scene reuse are preserved.
- `review.py`: render representative full notebook titles, explicitly request
  flat half-add expansion, retain unresized PNGs, and reject oversized or
  undersized-type notebook views. Real overlays still call the published
  `PnrResult.net_parasitics()` on the actual cell library (`library_mock=false`);
  no synthetic C, pin-C substitution, or new signoff claim.

## Visual loop

1. Opened the round-9 screenshots and froze the prior SVG/PDF/PNG files.
   Confirmed the intrinsic 1440 px half-adder and tiny native adder/minmax keys.
2. Rebalanced the half-adder and enlarged type; rendered half, adder and
   minmax, then all four notebook views. Automated checks identified the two
   larger-font gallery collisions above; fixed and rendered again.
3. Rendered all 22 gallery + four notebook PNGs at exactly 1000 px. Opened
   every image. Narrowed the adder side key from 248 to 208 px after review.
4. Rendered the final set and opened all final gallery PNGs, all four notebook
   previews, and all four unresized notebook PNGs. Reopened the four final
   1000 px notebook previews after publishing comparisons. No remaining
   defects observed. The geometric and text audits pass throughout.

Across all final gallery/notebook scenes: **0 short jogs, 0 rotated gates,
0 symbol-edge runs, 0 clearance violations**. Framed copies keep their exact
standalone interior and parent routing stays outside frames.

## Objective gallery metrics — phase 5 → phase 6

Length is unique drawing-wire length, not chip micrometres. Bends exclude
T joins. Aspect includes annotation keys. The frozen phase-5 comparison lives
in `assets/phase5_metrics.json`; original baseline history remains in manifests.

| Figure | Wire px | Bends total | Bends/net mean | Bends/net max | Crossings | Aspect | Min font pt @1000px |
|---|---:|---:|---:|---:|---:|---:|---:|
| half_add-hierarchical | 3648 → 3104 | 8 → 8 | 0.89 → 0.89 | 2 → 2 | 5 → 2 | 2.54 → 2.54 | 9.0 → 11.0 |
| half_add-flat | 3648 → 3104 | 8 → 8 | 0.89 → 0.89 | 2 → 2 | 5 → 2 | 2.54 → 2.54 | 9.0 → 11.0 |
| full_add-hierarchical | 1344 → 1344 | 8 → 8 | 0.89 → 0.89 | 4 → 4 | 0 → 0 | 4.48 → 4.48 | 9.0 → 11.0 |
| full_add-flat | 11072 → 10192 | 30 → 30 | 1.58 → 1.58 | 5 → 5 | 12 → 6 | 3.66 → 3.61 | 9.0 → 9.0 |
| adder2-hierarchical | 512 → 480 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.58 → 1.51 | 10.0 → 17.2 |
| adder2-flat | 24768 → 23040 | 64 → 64 | 1.73 → 1.73 | 7 → 7 | 29 → 17 | 1.83 → 1.80 | 9.0 → 9.0 |
| adder4-hierarchical | 960 → 864 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 2.64 → 2.42 | 9.0 → 11.0 |
| adder4-flat | 52224 → 48800 | 132 → 132 | 1.81 → 1.81 | 7 → 7 | 63 → 39 | 0.90 → 0.89 | 9.0 → 9.0 |
| mul1-hierarchical | 1808 → 1808 | 8 → 8 | 1.33 → 1.33 | 2 → 2 | 2 → 2 | 2.64 → 2.64 | 9.0 → 11.1 |
| mul1-flat | 1808 → 1808 | 8 → 8 | 1.33 → 1.33 | 2 → 2 | 2 → 2 | 2.64 → 2.64 | 9.0 → 11.1 |
| mac1-hierarchical | 3224 → 3224 | 12 → 12 | 0.92 → 0.92 | 3 → 3 | 2 → 2 | 3.09 → 3.09 | 9.0 → 11.0 |
| mac1-flat | 17696 → 16912 | 56 → 56 | 2.07 → 2.07 | 8 → 8 | 16 → 10 | 2.14 → 2.07 | 9.0 → 9.0 |
| sign-hierarchical | 592 → 592 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 1.45 → 1.45 | 12.4 → 20.2 |
| sign-flat | 592 → 592 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 1.45 → 1.45 | 12.4 → 20.2 |
| compare2-hierarchical | 2728 → 2728 | 8 → 8 | 0.57 → 0.57 | 4 → 4 | 0 → 0 | 3.69 → 3.75 | 9.0 → 11.0 |
| compare2-flat | 2728 → 2728 | 8 → 8 | 0.57 → 0.57 | 4 → 4 | 0 → 0 | 3.69 → 3.75 | 9.0 → 11.0 |
| mul2-hierarchical | 5648 → 5648 | 24 → 24 | 2.00 → 2.00 | 4 → 4 | 7 → 7 | 2.55 → 2.55 | 9.0 → 11.0 |
| mul2-flat | 29152 → 28384 | 76 → 74 | 2.24 → 2.18 | 9 → 9 | 26 → 19 | 2.29 → 2.32 | 9.0 → 9.0 |
| minmax-hierarchical | 1328 → 1328 | 4 → 4 | 0.67 → 0.67 | 2 → 2 | 2 → 2 | 1.96 → 1.96 | 9.2 → 14.9 |
| minmax-flat | 1328 → 1328 | 4 → 4 | 0.67 → 0.67 | 2 → 2 | 2 → 2 | 1.96 → 1.96 | 9.2 → 14.9 |
| half_add-overlay | 3648 → 3104 | 8 → 8 | 0.89 → 0.89 | 2 → 2 | 5 → 2 | 2.14 → 2.07 | 9.0 → 11.0 |
| legend | 0 → 0 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.74 → 1.74 | 9.0 → 11.0 |

## Validation and changed files

`python3 -m pytest tests/schematic -q` → **178 passed** (170 existing + 8 new).
The new `test_colab_size.py` tests the intrinsic SVG and unresized public PNG
bounds for all four half-adder overlays, actual PNR C, 11 pt type in every
notebook view, readable g0–g3/keys, trimmed adder content and unchanged overlay
scene identity. Existing connectivity, determinism, frame, wire and text
audits remain passing. Logs: `build/schematic-review/round6/tests-final.log`.

Changed source/review files (all under `tritflow/schematic/`):
`__init__.py`, `placement.py`, `routing.py`, `render.py`, `vector.py`,
`legend.py`, `gallery.py`, `review.py`, `README.md`.
Changed/generated owned assets: `assets/adder4.svg`, `assets/full_add.svg`,
`assets/full_add-flat.svg`, `assets/legend.svg`, `assets/metrics.md`,
`assets/review_metrics.json`; added `assets/phase5_metrics.json`.
Added `tests/schematic/test_colab_size.py`; updated this status file.
Generated evidence is confined to `build/schematic-review/`.

Reproduce using installed dependencies:

```bash
python3 -m pytest tests/schematic -q
python3 -m tritflow.schematic.review --output build/schematic-review/round6/after
```

No new interface request; FRONTEND's existing public delegates already work.
