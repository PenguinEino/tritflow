# SCHEM status

2026-10-18 — phase-3 review complete. All changes are in SCHEM-owned
source/test/status paths and generated `build/` artifacts. No shared source
edits, git-state changes, package installs or reference-tree modifications.

## Done — phase 3

1. **Every gate faces left to right.** Removed the downward gate path from
   placement and rendering. Folded half adders put `g_d`, `g_nd`, `g_s` in
   one right-facing lower row. Full-add, adder2/4-flat, mac1-flat and mul2-flat
   all use this arrangement. Port flags may still enter from above.
2. **The half-adder jog is gone.** `g_u.Y` and `g_c.B` share one horizontal
   track. The straight `g_t` → `g_d` trunk remains. The real-C overlay uses
   precisely this scene: **2,248 → 2,200 px, 11 → 9 bends, maximum 2/net**.
3. **No short stairs anywhere in the gallery.** Placement aligns actual
   connected pin rows, including the folded compare2 row. Routing tracks
   direction and distance since the last corner; it forbids short interior
   legs and immediate reversals that could disappear during edge merging.
   All 22 figures have **0 short jogs, 0 rotated gates, 0 symbol-edge runs**.
4. **Reviewed every PNG again.** Personally inspected hierarchical and flat
   half_add, full_add, adder2, adder4, mul1, mac1, sign, compare2, mul2,
   minmax, plus the legend and the real-PNR overlay. Every gate has clear
   right-facing pin stubs; no routed wire follows a symbol outline.
5. **The accepted ripple overview is preserved.** The adder4 hierarchical
   SVG is byte-identical to phase 2: one straight carry chain, formal module
   port names, local operand/sum flags, **0 bends and 0 crossings**.
6. **Metrics and regression coverage updated.** The gallery reports phase-2
   → phase-3 geometry and the three new audit counts for every item. Tests
   enforce these across every circuit/view, retain the original wire/bend
   budgets, check the direct `g_u` → `g_c.B` connection and distinguish
   jogs from terminal stubs, T joins and perpendicular pin contact.

## Decisions and measured tradeoffs

- The minimum leg between degree-two corners is one **gate input pitch,
  32 drawing pixels**. Pin access retains the finer 8-pixel coordinate raster.
  Terminal stubs and T joins are excluded from the jog count. This deliberately
  removes the reported 16-pixel jog as well as smaller stairs.
- Symbol-edge auditing counts positive wire overlap along the entire symbol
  and label keep-out boundary. Perpendicular terminal contact is allowed.
  Existing symbol-interior, overlap, connectivity and label tests still apply.
- Full-add flat remains **2.15:1**, with **44 → 31 bends**, **10 → 8 crossings**
  and **5,096 → 5,040 px** of wire. Adder4-flat has **194 → 137 bends** and
  **57 → 32 crossings**. These gains come from aligning pins before routing.
- The collapsed full-adder sum flag gets its own clear channel: wire length
  increases **912 → 1,072 px** (17.5%), while bends fall **12 → 8** and
  crossings stay zero. Mul2 wire length increases **40 px hierarchical** and
  **88 px flat** while bend counts fall. Adder2-flat's worst individual net
  increases **7 → 8 bends**; its total falls **94 → 69**, and crossings
  **23 → 16**. The table retains these tradeoffs.
- The real overlay still calls public `PnrResult.net_parasitics()` on the
  actual cell library (`library_mock: false`), reading `wire_capacitance_f`.
  Its nine logical nets total **447.7378164 fF**. The retained report is
  `build/schematic-review/physical/half_add.net_parasitics.json`. The gallery
  skips a new DRC/LVS run and makes no new signoff claim. Trit values are
  settled ideal logic; C is an uncalibrated wire estimate, separate from pin C.
- Original hierarchy alias handling remains: published HALF/FULL/MUL
  structures are verified by every cell and ordered terminal, then labelled
  with formal module ports. Arbitrary source metadata can override through
  `hierarchy={scope: {'module': type, 'ports': {formal: logical_net}}}`.
  Unknown structures retain their actual logical net names.
- Font family, nominal 8 pt gate labels, 0.6 pt outlines and trit colours
  continue to follow `figures/style.py`. Overlay tables reuse exact wire
  geometry and extend the canvas; they do not move symbols or reroute nets.

## Review artifacts

[SVG/PDF/PNG gallery](../../build/schematic-review/index.html) ·
[Geometry and audit comparison](../../build/schematic-review/metrics.md) ·
[Per-net manifest](../../build/schematic-review/manifest.json) ·
[Package/API guide](../../tritflow/schematic/README.md)

Repository review figures/data:
[full-add flat](../../tritflow/schematic/assets/full_add-flat.svg),
[full-add hierarchy](../../tritflow/schematic/assets/full_add.svg),
[adder4 hierarchy](../../tritflow/schematic/assets/adder4.svg),
[legend](../../tritflow/schematic/assets/legend.svg),
[current metrics](../../tritflow/schematic/assets/review_metrics.json),
[phase-2 baseline](../../tritflow/schematic/assets/phase2_metrics.json),
[original baseline](../../tritflow/schematic/assets/baseline_metrics.json).
The original gallery is retained in `build/schematic-before/`; the phase-2
set is retained in `build/schematic-phase2/`. Phase-2 wire, bend, crossing
and short-jog counts were independently recovered from all 22 retained SVGs
and agree with the frozen baseline. `manifest.json` keeps original `before`,
phase-2 `previous` and current `metrics` records.

## Every gallery item: phase 2 → phase 3

Wire length is in drawing pixels, not chip micrometres. A bend is a unique same-net degree-two orthogonal corner; T joins are excluded. Crossings count distinct different-net perpendicular intersections. Aspect is full canvas width / height; the real-C overlay includes its annotation table.

| Figure | Wire px | Bends total | Bends/net mean | Bends/net max | Crossings | Aspect |
|---|---:|---:|---:|---:|---:|---:|
| half_add-hierarchical | 2248 → 2200 | 11 → 9 | 1.22 → 1.00 | 2 → 2 | 5 → 5 | 1.68 → 1.68 |
| half_add-flat | 2248 → 2200 | 11 → 9 | 1.22 → 1.00 | 2 → 2 | 5 → 5 | 1.68 → 1.68 |
| full_add-hierarchical | 912 → 1072 | 12 → 8 | 1.33 → 0.89 | 4 → 4 | 0 → 0 | 1.69 → 1.85 |
| full_add-flat | 5096 → 5040 | 44 → 31 | 2.32 → 1.63 | 6 → 6 | 10 → 8 | 2.15 → 2.15 |
| adder2-hierarchical | 448 → 448 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.28 → 1.28 |
| adder2-flat | 11208 → 11152 | 94 → 69 | 2.54 → 1.86 | 7 → 8 | 23 → 16 | 1.13 → 1.13 |
| adder4-hierarchical | 864 → 864 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 2.12 → 2.12 |
| adder4-flat | 23944 → 23856 | 194 → 137 | 2.66 → 1.88 | 9 → 8 | 57 → 32 | 2.16 → 2.16 |
| mul1-hierarchical | 1152 → 1152 | 9 → 9 | 1.50 → 1.50 | 3 → 3 | 2 → 2 | 1.67 → 1.67 |
| mul1-flat | 1152 → 1152 | 9 → 9 | 1.50 → 1.50 | 3 → 3 | 2 → 2 | 1.67 → 1.67 |
| mac1-hierarchical | 2176 → 2176 | 12 → 12 | 0.92 → 0.92 | 3 → 3 | 3 → 3 | 2.32 → 2.32 |
| mac1-flat | 6944 → 6920 | 55 → 42 | 2.04 → 1.56 | 6 → 6 | 12 → 10 | 2.72 → 2.72 |
| sign-hierarchical | 312 → 312 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 0.83 → 0.83 |
| sign-flat | 312 → 312 | 2 → 2 | 0.67 → 0.67 | 2 → 2 | 0 → 0 | 0.83 → 0.83 |
| compare2-hierarchical | 3080 → 3048 | 15 → 9 | 1.07 → 0.64 | 4 → 4 | 3 → 3 | 1.27 → 1.27 |
| compare2-flat | 3080 → 3048 | 15 → 9 | 1.07 → 0.64 | 4 → 4 | 3 → 3 | 1.27 → 1.27 |
| mul2-hierarchical | 2808 → 2848 | 27 → 23 | 2.25 → 1.92 | 4 → 3 | 7 → 7 | 1.74 → 1.74 |
| mul2-flat | 13944 → 14032 | 84 → 71 | 2.47 → 2.09 | 7 → 7 | 24 → 21 | 1.47 → 1.47 |
| minmax-hierarchical | 768 → 768 | 5 → 5 | 0.83 → 0.83 | 3 → 3 | 2 → 2 | 1.23 → 1.23 |
| minmax-flat | 768 → 768 | 5 → 5 | 0.83 → 0.83 | 3 → 3 | 2 → 2 | 1.23 → 1.23 |
| half_add-overlay | 2248 → 2200 | 11 → 9 | 1.22 → 1.00 | 2 → 2 | 5 → 5 | 1.44 → 1.44 |
| legend | 0 → 0 | 0 → 0 | 0.00 → 0.00 | 0 → 0 | 0 → 0 | 1.74 → 1.74 |

A short jog is a leg shorter than one gate input pitch (32 px) between two degree-two corners. Terminal stubs and T joins are excluded; pin access uses the finer 8 px raster. Edge runs count positive overlap along any symbol/label keep-out boundary; perpendicular pin contact is allowed.

| Figure | Short jogs | Rotated gates | Symbol-edge runs |
|---|---:|---:|---:|
| half_add-hierarchical | 1 → 0 | 0 → 0 | 0 → 0 |
| half_add-flat | 1 → 0 | 0 → 0 | 0 → 0 |
| full_add-hierarchical | 2 → 0 | 0 → 0 | 0 → 0 |
| full_add-flat | 4 → 0 | 2 → 0 | 0 → 0 |
| adder2-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 |
| adder2-flat | 9 → 0 | 4 → 0 | 0 → 0 |
| adder4-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 |
| adder4-flat | 19 → 0 | 8 → 0 | 0 → 0 |
| mul1-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 |
| mul1-flat | 0 → 0 | 0 → 0 | 0 → 0 |
| mac1-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 |
| mac1-flat | 4 → 0 | 2 → 0 | 0 → 0 |
| sign-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 |
| sign-flat | 0 → 0 | 0 → 0 | 0 → 0 |
| compare2-hierarchical | 3 → 0 | 0 → 0 | 0 → 0 |
| compare2-flat | 3 → 0 | 0 → 0 | 0 → 0 |
| mul2-hierarchical | 3 → 0 | 0 → 0 | 0 → 0 |
| mul2-flat | 5 → 0 | 2 → 0 | 0 → 0 |
| minmax-hierarchical | 0 → 0 | 0 → 0 | 0 → 0 |
| minmax-flat | 0 → 0 | 0 → 0 | 0 → 0 |
| half_add-overlay | 1 → 0 | 0 → 0 | 0 → 0 |
| legend | 0 → 0 | 0 → 0 | 0 → 0 |

## Tests and regeneration

```bash
python3 -m pytest tests/schematic -q
# 101 passed, including real-cell-library PNR integration.
python3 -m compileall -q tritflow/schematic
python3 -m tritflow.schematic.gallery --output build/schematic-review
```

The suite checks exact terminal accounting and connected routes, deterministic
port/instance reordering, grid alignment, symbol/label clearance, no shared
edges between different nets, hierarchy expansion and source port aliases.
Fresh-process SVG and PDF hashes match at PYTHONHASHSEED=1,42,123 for half_add,
full_add-flat, adder4-flat and mul2-flat. No dependency was added.

## Interface requests — FRONTEND/integrator

The `SynthesizedNetlist.schematic(**options)` delegate and notebook stage are
now present in the shared checkout. `sch.annotate(inputs=...)` and
`sch.annotate(parasitics=lay.result)` retain the scene; `sch.metrics` exposes
all geometry and audit counts. No shared API change is needed for phase 3.

Optional existing request: retain a public scope → module / formal-port map
through synthesis for arbitrary authored modules and pass it as `hierarchy=`.
Verified published arithmetic already has correct port names; this is not a
blocker for the gallery.

## In progress / blockers

None within SCHEM scope. Phase-3 implementation, gallery inspection and tests
are complete.
