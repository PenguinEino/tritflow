# SCHEM_ROUTE

Complete, 2026-10-22. No blockers or interface requests.

## Result

All 18 combinational `examples/*.tv` files and both notebook sources in the
brief synthesize and draw with
`.schematic(net_names=True, expand="*", title="", legend=False)._repr_svg_()`.
Every case passes independent wire, symbol, pin, junction, text and electrical
connectivity checks. There are no short jogs or ambiguous foreign crossings.
Value colouring, annotation scene reuse and exact `data-net` attributes remain
intact. Final full run: **248 passed, 592 deselected in 147.95 seconds**.

All 12 cases that drew before this work produce byte-identical expanded SVGs.
This includes `half_add.tv`, `full_add.tv` and `adder2.tv`; their before/after
SHA-256 values are also enforced by regression tests. No recorded results,
schematic assets or physical-design code were changed.

## Cause

The generic placer folded deep RTL logic into earlier columns, with at most
three cells per column and a fixed horizontal gap. Fanout rails, pin approaches
and local port flags consumed the available channels. The existing retry only
changed net order on that same crowded placement.

The original two-input pin offsets also differ from the output by 16 pixels,
half the required 32-pixel bend leg. Dense reconvergent paths could trap an
approach even while nearby routes respected the spacing rules. Widening the
sheet alone did not reliably solve this.

## Fix and decisions

1. Keep the original arithmetic placement and routing as the first attempt,
   including its route-order retry. Reusable framed arithmetic templates and
   their internal routes are preserved.
2. After congestion, unfold generic logic into one column per dependency
   level. Increase row/column pitch on successive passes and allow a lane per
   outgoing fanout bus in busy columns. Pins use a common 32-pixel lattice;
   two-input separation becomes 64 pixels. Internal orthogonal adapters meet
   the unchanged gate outlines.
3. Reserve each fanout rail's driver feed before load routing. Keep the rail
   itself separate from its feed when reporting/pruning trunks. Wider retries
   use distance to the actual net tree, a heuristic weight of two, and a
   200,000-state budget per connection. Compact drawings keep their original
   unweighted search and order.
4. If wider searches still fail, assign channel tracks deterministically.
   Adjacent levels connect locally; long nets use interval-coloured horizontal
   tracks above the logic. Source and receiver lanes stay separate. Unary
   inputs also get staggered approaches in this final pass, so foreign pin
   leads cannot overlap horizontally. This handles `alu9` without circuit-name
   or net-name special cases.
5. Detailed fallback drawings preserve 12 pt native type and readable strokes,
   with scroll/zoom. Enlarging labels to force the whole circuit into a
   1000-pixel overview had made labels larger than gate bodies. Reviewed
   compact notebook figures keep their original sizing. `scene.notes` records
   the fallback used.

The connection-test helper now splits merged wires at rendered same-net
junctions as well as segment endpoints: a four-way join can lie inside both
merged segments. Glyph-clearance checking was factored into a shared helper
and reused for the new designs.

## Before / after

The other 12 review cases remain byte-identical. Canvas sizes below are SVG
viewBox units, before the 0.8 native display scale for detailed views.

| Case | Cells | Before | After canvas | Routing pass |
|---|---:|---|---:|---|
| notebook `add2` | 23 | channel failure at `s[0]` | 4816 × 1168 | wider 1 |
| notebook `mul_table` | 32 | channel failure at `_n17` | 5088 × 1504 | wider 1 |
| `case_table` | 32 | channel failure at `_n17` | 5088 × 1504 | wider 1 |
| `mux_rtl` | 32 | channel failure at `b` | 4752 × 1776 | wider 1 |
| `comparator_rtl` | 27 | channel failure at `_n15` | 3840 × 1424 | wider 1 |
| `adder4_rtl` | 55 | channel failure at `_n37` | 8928 × 2512 | wider 1 |
| `alu` | 64 | channel failure at `_n4` | 10272 × 3040 | wider 2 |
| `alu9` | 262 | channel failure at `_n27` | 26448 × 7408 | assigned tracks |

`full_add_rtl` uses the original arithmetic template. `alu9` takes about
30 seconds including failed searches, rasterization and metric collection on
this machine. The smaller newly supported cases take roughly 2–7 seconds.
Local channel routing reduced the large fallback from 10,133 to 4,623 marked
crossings and reduced its width by 26% compared with sending every net through
the upper tracks.

## Images and visual review

- [Final review index](../../build/schem-route/final/index.html): 20 SVGs,
  20 overview PNGs and 24 native-scale left/middle/right detail PNGs.
- [Metrics and hashes](../../build/schem-route/final/results.json).
- [Notebook add2](../../build/schem-route/final/add2.png),
  [case table](../../build/schem-route/final/mul_table.png),
  [ALU](../../build/schem-route/final/alu.png),
  [ALU9](../../build/schem-route/final/alu9.png).
- [ALU9 detail](../../build/schem-route/final/alu9-middle.png) shows the final
  local channels, staggered unary approaches and crossing gaps at native scale.
- Baseline SVGs/PNGs and exact exceptions: `build/schem-route/before/`.
- Intermediate reviews: `build/schem-route/iteration*/`. Failed maze iterations
  have no complete SVG.

Images were rendered from SVG using the already-installed CairoSVG and opened
with the image viewer after each drawing change. Final review covered every
overview plus native-scale details of the new layouts. Intermediate review
exposed oversized text and local-route overlap; both were corrected and
checked again. Final text, pin approaches and branch dots are clear. Foreign
crossings have straight runs on both sides and white gaps.

## Validation and reproduction

```bash
export TR1UM_PDK="$HOME/pdk/TR-1um-pinned"
python3 -m pytest tests -k schematic -q
PYTHONPATH=. python3 tests/schematic/test_synthesized.py build/schem-route/final
```

The new tests cover all 20 designs, value colours and JavaScript net identifiers,
exact reviewed SVG hashes, input-order determinism, straight foreign crossings,
and forced track fallback with constants, unused inputs and repeated gate pins.

## What remains / scope

No required work remains. Large detailed RTL views require scrolling or zooming
when individual labels must be read; the 1000-pixel overview is for orientation.
Hierarchical arithmetic views retain their compact presentation. Novel composed
macro routing still uses the original template-preserving router.

No packages installed, network access, publishing, sign-in, PDK/reference-tree
changes, git commits/pushes, or edits to `sim`, `pnr`, `extract`, `cells`,
recorded results, or other streams' files.
