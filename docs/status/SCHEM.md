# SCHEM status

2026-10-18 — integrator gallery revision implemented and ready for review.
All work stays in SCHEM-owned source/test/status paths and generated `build/`
artifacts. No shared source edits, git-state changes, or package installs.

## Done — response to the concrete review

1. **Straight ripple overview.** All digit blocks share one row. The carry
   connection is a straight `cout` → `cin` track. Each digit's `a[i]` / `b[i]`
   flags sit immediately above their consumers and `sum[i]` immediately below
   its producer. Formal names replace anonymous internal net names inside the
   blocks. Four-trit overview: **0 crossings, 0 bends**, 864 px of wire versus
   16,112 px before (94.6% shorter).
2. **Compact full-adder flat view.** Two light half-adder frames sit side by
   side, each containing exactly its seven real cells. A downward NANY marks
   a folded feedforward row. Aspect changed **6.87:1 → 2.15:1**, wire length
   **14,112 → 5,096 px**, bends **69 → 44**. Larger flat adders use several rows
   of these panels instead of a single very wide strip.
3. **Half-adder trunk and shared channels.** `g_t` → `g_d` is one straight
   horizontal trunk, with a proper branch to `g_u`. Every net meets the target
   **≤2 bends/net** (previous maximum 8). Wire length **5,152 → 2,248 px**
   (56.4% shorter). Fanout attaches to existing trees rather than allocating
   a separate route per load. Bend-aware A* protects symbol and terminal
   access, shares routing channels, and permits only unconnected straight
   crossings between different nets.
4. **Paper style.** Serif font preferences, ternary colours, nominal 8 pt gate
   labels, 0.6 pt symbol outlines and 1.2 pt signals follow `figures/style.py`.
   Frame headers replace repeated cramped scope labels on individual gates.
5. **Real PNR overlay.** The gallery now runs the actual cell library through
   public PNR, calls `PnrResult.net_parasitics()`, and reads only
   `wire_capacitance_f`. There is **no synthetic gallery capacitance**. The
   half-adder's nine logical nets total **447.7378164 fF** of estimated routed
   wire C. Retained provenance: `build/schematic-review/physical/half_add.*`;
   the manifest records `library_mock: false` and the report schema. The
   gallery skips a new DRC/LVS run and makes no new signoff claim.
6. **Objective review.** Added `Schematic.metrics`, a frozen original baseline,
   per-net details and before/after results for every gallery item. Tests
   enforce shorter wire length, nonincreasing bend counts, compact aspect,
   local ripple ports, exact aliases, frame membership and the half-adder
   bend target. All **22 final PNGs were personally inspected again**, including
   both views of every requested design, the legend and the real-C overlay.

## Decisions and limits

- The shared mapped netlist still does not serialize source module types or
  formal port aliases. For published HALF/FULL/MUL structures, SCHEM verifies
  **every cell and ordered terminal** against small circuit grammars, then
  uses their standard port names. Recognition does not rely on gate names,
  anonymous net names or truth tables alone. Renaming instances is tested;
  changing a gate function invalidates the match.
- Arbitrary module aliases are supported now through
  `draw(net, hierarchy={scope: {'module': type, 'ports': {formal: logical_net}}})`.
  Supplied source metadata overrides recognized labels. Unknown or rewritten
  modules without metadata retain exact logical net names. No source-parser
  internals or other-stream changes are needed to draw them.
- Ports follow consumer/producer positions; natural bit order breaks ties.
  This intentionally replaces global alphabetical input/output columns.
- Annotation views share the exact same symbol/wire scene. Names, trits and
  fF values appear in a compact keyed table below it, with coloured wire
  swatches and SVG net hover titles. The canvas extends for this table;
  no extra blank routing gutters, overlapping inline captions or rerouting.
- Crossing/bend tradeoffs remain explicit. Standalone half-adder crossings
  increase **4 → 5** while meeting ≤2 bends/net; flat mul2 crossings increase
  **23 → 24** while halving wire length and reducing bends. The flat full
  adder keeps 10 crossings. All are drawn as gaps, never junction dots. These
  increases are retained in the report rather than hidden by an aggregate.
- Geometry metrics are drawing pixels, not physical chip µm. Trit values are
  settled ideal logic; wire C is PNR's uncalibrated estimate, separate from
  receiving-pin C and total load. No electrical results are inferred from
  drawing geometry.

## Review artifacts

[Interactive-size SVG/PDF/PNG index](../../build/schematic-review/index.html) ·
[Full comparison](../../build/schematic-review/metrics.md) ·
[Per-net manifest](../../build/schematic-review/manifest.json) ·
[Package/API guide](../../tritflow/schematic/README.md)

Repository review figures/data:
[straight adder4](../../tritflow/schematic/assets/adder4.svg),
[full-adder flat](../../tritflow/schematic/assets/full_add-flat.svg),
[legend](../../tritflow/schematic/assets/legend.svg),
[original baseline](../../tritflow/schematic/assets/baseline_metrics.json),
[current metrics](../../tritflow/schematic/assets/review_metrics.json).
The original PNG/SVG/PDF review set was preserved under `build/schematic-before/`.

## Every gallery item: original → revised

Bends count same-net degree-two orthogonal corners; T joins are excluded.
Crossings count distinct perpendicular intersections of different nets.
Aspect is canvas width / height (including the overlay's table). Legend has
no circuit nets. The old overlay's synthetic values are not compared; this
is a geometry comparison, and the revised overlay uses the real PNR report.

| Figure | Wire px | Bends total | Bends/net mean | Bends/net max | Crossings | Aspect |
|---|---:|---:|---:|---:|---:|---:|
| half_add-hierarchical | 5152 → 2248 | 25 → 11 | 2.78 → 1.22 | 8 → 2 | 4 → 5 | 4.87 → 1.68 |
| half_add-flat | 5152 → 2248 | 25 → 11 | 2.78 → 1.22 | 8 → 2 | 4 → 5 | 4.87 → 1.68 |
| full_add-hierarchical | 3360 → 912 | 20 → 12 | 2.22 → 1.33 | 4 → 4 | 0 → 0 | 3.75 → 1.69 |
| full_add-flat | 14112 → 5096 | 69 → 44 | 3.63 → 2.32 | 12 → 6 | 10 → 10 | 6.87 → 2.15 |
| adder2-hierarchical | 4272 → 448 | 26 → 0 | 2.89 → 0.00 | 6 → 0 | 5 → 0 | 1.95 → 1.28 |
| adder2-flat | 39240 → 11208 | 162 → 94 | 4.38 → 2.54 | 20 → 7 | 29 → 23 | 6.66 → 1.13 |
| adder4-hierarchical | 16112 → 864 | 78 → 0 | 4.59 → 0.00 | 10 → 0 | 27 → 0 | 2.17 → 2.12 |
| adder4-flat | 130632 → 23944 | 471 → 194 | 6.45 → 2.66 | 36 → 9 | 85 → 57 | 6.83 → 2.16 |
| mul1-hierarchical | 1920 → 1152 | 14 → 9 | 2.33 → 1.50 | 4 → 3 | 2 → 2 | 3.15 → 1.67 |
| mul1-flat | 1920 → 1152 | 14 → 9 | 2.33 → 1.50 | 4 → 3 | 2 → 2 | 3.15 → 1.67 |
| mac1-hierarchical | 8304 → 2176 | 43 → 12 | 3.31 → 0.92 | 6 → 3 | 4 → 3 | 3.26 → 2.32 |
| mac1-flat | 34216 → 6944 | 134 → 55 | 4.96 → 2.04 | 22 → 6 | 17 → 12 | 8.33 → 2.72 |
| sign-hierarchical | 848 → 312 | 4 → 2 | 1.33 → 0.67 | 2 → 2 | 0 → 0 | 1.92 → 0.83 |
| sign-flat | 848 → 312 | 4 → 2 | 1.33 → 0.67 | 2 → 2 | 0 → 0 | 1.92 → 0.83 |
| compare2-hierarchical | 4848 → 3080 | 24 → 15 | 1.71 → 1.07 | 4 → 4 | 5 → 3 | 4.62 → 1.27 |
| compare2-flat | 4848 → 3080 | 24 → 15 | 1.71 → 1.07 | 4 → 4 | 5 → 3 | 4.62 → 1.27 |
| mul2-hierarchical | 6048 → 2808 | 30 → 27 | 2.50 → 2.25 | 4 → 4 | 9 → 7 | 1.88 → 1.74 |
| mul2-flat | 28080 → 13944 | 116 → 84 | 3.41 → 2.47 | 16 → 7 | 23 → 24 | 3.19 → 1.47 |
| minmax-hierarchical | 1520 → 768 | 6 → 5 | 1.00 → 0.83 | 2 → 3 | 2 → 2 | 2.50 → 1.23 |
| minmax-flat | 1520 → 768 | 6 → 5 | 1.00 → 0.83 | 2 → 3 | 2 → 2 | 2.50 → 1.23 |
| half_add-overlay | 5152 → 2248 | 25 → 11 | 2.78 → 1.22 | 8 → 2 | 4 → 5 | 4.87 → 1.44 |
| legend | 0 → 0 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.74 → 1.74 |

## Tests and regeneration

```bash
python3 -m pytest tests/schematic -q
# 80 passed in the final run, including real-cell-library PNR integration.
python3 -m compileall -q tritflow/schematic
python3 -m tritflow.schematic.gallery --output build/schematic-review
```

The suite also checks determinism under port/instance reordering, exact terminal
accounting and connected routes, no symbol overlap/wire-through-symbol,
no shared edges between different nets, grid alignment, no label overlap or
clipping with all overlays, XML escaping, invalid inputs, explicit source port
metadata, selective hierarchy and non-convex scope handling. SVG/PDF use the
same vector paths; no new system or Python dependency was introduced. Revised SVG and PDF bytes
also match across fresh processes with PYTHONHASHSEED=1, 42 and 123.

## Interface requests — FRONTEND/integrator

The public hook remains `tritflow.schematic.draw(net, **options)`. Add this
one delegate to `SynthesizedNetlist`, inherited by `flow.Netlist`:

```python
def schematic(self, **options):
    from tritflow.schematic import draw
    return draw(self, **options)
```

Display the result between synthesis and P&R. `sch.annotate(inputs=...)` and
`sch.annotate(parasitics=lay.result)` reuse the same scene; `sch.metrics`
provides geometry review data. The gallery entry point is reproducible from
committed sources and the real cell library.

For arbitrary authored module port aliases, preserve a public scope → module /
formal-port-to-logical-net map through elaboration and synthesis, then pass it
as the supported `hierarchy=` argument. Existing published arithmetic is already
correct through exact structural recognition; this metadata request is not a
blocker for the current gallery.

## Blockers

None within SCHEM scope. Visual review and all requested owned implementation
work are complete; no other stream's files were changed.
