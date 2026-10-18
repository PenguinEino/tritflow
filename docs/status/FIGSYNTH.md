# FIGSYNTH status

Redraw and integrator-requested padding polish completed 2026-10-19.

## Done / decisions

- Updated only `figures/fig_synth.py`, this status file, and the three authorized
  `figures/out/fig_synth.{png,pdf,svg}` outputs. No helper file was needed.
- Kept panel (a)'s HDL, with whitespace-only wrapping of the two half-adder
  instantiations so the source stays inside its column.
- Read the actual half/full-adder HDL with `figures/data.py` (including `FIG_REF`),
  synthesize it in memory, evaluate the nets, and derive all displayed cell counts
  from those circuits. No dependency on ignored `build/` reports.
- Half-adder columns are logic levels 1–6; both diagrams share column pitch
  1.75 and row pitch 1.6. Full-adder macros occupy columns 1 and 3 on row 0;
  carry-merge primitives occupy columns 5 and 6 on row 1. All primitive boxes
  have the same dimensions and rendered size across panels. Input pins have
  distinct landing points; NANY pins show A/B explicitly.
- Primitive boxes are 1.24 × 0.88 drawing units; both half-adder macros are
  2.65 × 1.70. Central labels have at least 0.6 em padding **inside the border
  stroke**, enforced by `check_label_padding()` on every render. Pin names
  occupy separate positions with clearance from central text and all wires.
- One crossover is necessary with all four ports on the exterior: the actual
  half-adder graph is planar, but adding an exterior vertex connected to `a`,
  `b`, `sum`, and `carry` makes it nonplanar (checked with NetworkX). The single
  allowed crossing is between the vertical `a` branch and horizontal `b` net;
  the `a` branch has an explicit gap. Other half-adder nets and all full-adder
  nets have no crossings. The augmented graph contains a subdivision of K3,3
  with partitions `{g_t, g_c, exterior}` and `{a, g_u, g_d}`: exterior reaches
  `g_u` through `b`, reaches `g_d` through `g_s/g_nd`, and `a` reaches `g_c`
  through `g_na`.
- Source code, legend, trit palette, a=b=+1 example and the identity
  `2 = (−1) + 3·(+1)` are retained. The full-adder sum path stays horizontal
  through ha1 → ha2 → output. Inputs and outputs share left/right columns.

## Before / after visual loop

- **Viewed** the original PNG: curved fan-out crosses at the inputs and tangles
  along the NANY chain; primitive instance names and pin identities are absent.
  The full-adder blocks have different top edges and curved sum/carry routes.
  Long source lines consume the gutter; displayed cell counts are literals.
- First Manhattan redraw: identified crowded pin/cell labels, macro port labels
  colliding with body text, a junction dot at a bend instead of its branch,
  and different physical primitive heights between the two axes.
- Second redraw: moved pin labels outside the primitive boxes, kept small macro
  carry labels inside the upper corner, corrected the `t` branch/dot, and
  matched axis scaling. Review found `c2` touching its vertical wire; moved it.
- Final redraw: aligned both diagrams to the same grid and port columns.
  **Viewed** both the final 600-dpi PNG and a 1007-pixel-wide notebook preview.
  No remaining overlaps, tangles, inconsistent cell sizes or arbitrary heights.
- Regenerated only this figure through the existing `style.save` function.

## Integrator polish pass

- Re-viewed the initial redraw after feedback about border crowding. Measured
  horizontal margins: NANY labels had only 0.28 em, and macro labels 0.44 em.
  The first pass's no-overlap check did not enforce adequate interior padding.
- Widened the primitive boxes and diagram columns, enlarged macro height,
  moved carry pins into their own upper corner, and offset pin letters from
  their wires. Adjusted nearby bends to preserve clearance without crossings.
  Font sizes remain 5.9 pt source / 6.2 pt cells / 7 pt ports / 7.5 pt titles.
- Reduced figure height from 4.10 to 3.25 inches (21% shorter). The two diagrams
  use equal 38%-height axes, and their width increases from 57% to 66%; the code
  column uses 30%. This removes much of the empty area below panel (a).
- Viewed the polished 600-dpi PNG and the 1007-pixel-wide notebook preview.
  Checked every label against the border's inner stroke edge; moved three
  input-wire bends once more to obtain at least 2 pt pin-to-wire clearance.
  Final review: no touching labels, wire/text overlaps or inconsistent sizes.

## In progress

- None.

## Blockers / interface requests

- None. No packages installed; no changes to shared interfaces.

## Validation / how to reproduce

- Render only this figure: `PYTHONPATH=. python3 figures/fig_synth.py`.
- No figure tests currently exist under `figures/` or `tests/`.
- Existing relevant checks:
  `python3 -m pytest tests/synth/test_synthesis.py tests/synth/test_writers.py tests/synth/test_build_all.py -q`
  → **83 passed** again after the polish (2.04 s). No P&R, simulation or other
  figure regeneration.
- One-off independent geometry/electrical audit (`/tmp/check_fig_synth.py` in
  this session): evaluated every wire's trit signature across all 9 half-adder
  and 27 full-adder inputs, matched every drawn pin to the actual HDL net,
  checked connected routes (bridging only the intentional `a` gap), checked
  every branch for its junction dot, and rejected foreign-net contacts and
  wire/box intersections. **Passed**; exactly one intentional gapped crossing
  in (b), zero in (c). Integer sum/carry identity passes every vector.
- Repeated the full geometry/electrical audit after the polish: all 36 input
  combinations pass; one intentional gap in (b), no crossings in (c).
- 600-dpi renderer audit (`/tmp/check_fig_synth_padding.py` in this session):
  **zero text/text and wire/text overlaps**, matching primitive sizes in both
  panels, and **2.038 pt minimum pin-letter-to-wire clearance** including wire
  and tick stroke widths. Minimum interior margins, after border-stroke width:

  | Label group | Minimum padding |
  |---|---:|
  | NANY primitives | 0.697 em |
  | INV `g_na`, `g_nd` | 0.828 em |
  | INV `g_cout` | 0.779 em |
  | `ha1`, `ha2` | 1.029 em |

- Two additional isolated renders produce byte-identical PNG/PDF/SVG files.
  SVG identifiers are unique. Current SHA-256:
  - PNG: `fe983a6600f6d1eff17489fb50402ad3700352e577b9379467bc95dde6b07644`
  - PDF: `7b4b2a7d73c14b234ad171e0f01258e14f87840a05f32a074522794e189b02d8`
  - SVG: `ed04c8a9c9441881462711f74998ad636b4f17c1bbc8b7f7650641b6a499694e`
- Python/status whitespace checks pass. Generated SVG keeps Matplotlib's
  normal path-data whitespace, as emitted by shared `style.save`.
- No commits or git-state operations; other streams' files left untouched.
