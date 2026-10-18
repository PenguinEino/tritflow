# PNR stream — phase 3

## Done

The four shared designs are routed with the **132 µm compact cell library**.
All canonical GDS, PNR JSON, official DRC reports, strict LVS reports/extracted
SPICE, seed comparisons and notebook views are under `build/<design>/`.
The generated result/seed tables below are refreshed by `examples/pnr_all.py`.
Phase-1 `/tmp` artifacts are superseded by these project-local results.

- API and CLI: seeded placement, HPWL annealing/history, M1 horizontal channel
  routing, M2 vertical routing, rip-up/reordering, adaptive horizontal channels
  and vertical signal corridors, hierarchical GDS and geometric self-checks.
- Compact cells: retain `free_M2_tracks` metadata, honor actual M2/V1 obstruction
  rectangles and certified free columns, reflect all constraints with MY, and
  select an unobstructed advertised signal-pin access. No implicit assumption
  that cell interiors are M2-free remains.
- Four physical builds compared at **seeds 0, 7, 19**, **600 annealing steps**.
  Every seed is routed and checked by the unmodified PDK drawing-layer DRC and
  strict device-level LVS through the SIM stream's existing extraction API.
- `examples/pnr_all.py` detects changed cell publications, restarts a run when
  inputs change mid-build, and reuses results only when both input hashes and
  checked output hashes agree. Deleted/edited GDS or reports trigger rebuilding.
- `tritflow.viz.layout` provides the KLayout raster with embedded layer legend,
  Plotly net/instance selection, placement + HPWL animation, and routing replay.
  Figures are normal notebook-ready Plotly Figures; exported HTML embeds Plotly.

## In progress / blockers

Phase-3 compact, near-square builds are complete. All four canonical designs
and all twelve seed candidates pass drawn connectivity, routing DRC, official
PDK DRC and strict LVS. All canonical aspect ratios are ≤1.5 and utilization
is ≥45%. See the generated before/after and timing tables below.
No blockers; no background PNR processes are left running.

## Decisions and physical scope

**Routing constraints.** CELLS publishes `free_M2_tracks: {x, count, wire_width,
clearance}` in each abstract. The loader normalizes that to `Cell.free_tracks.M2`
and preserves the metadata in PNR JSON. Explicit M2 obstructions remain
mandatory even on a declared free column. Internal V1 cuts imply their M2
metal enclosure before spacing is applied; neither signal wire nor new landing
may occupy that metal. `free_tracks.M2` and `routing.m2_free_tracks` are also
accepted for explicit/mock libraries. An absent free-column list uses shape
constraints alone; an empty list forbids full-height over-cell transit.

M2/V1 obstruction boundaries and interior points are included in the maze's y
coordinates. This prevents compressed vertical graph edges from jumping over
an obstacle between channel or pin coordinates. Via cuts are 1.4 µm with 1 µm
metal enclosure; signal landings are 3.4 µm square. Signal M1/M2 wires use
1.8/3.0 µm widths, with conservative 3.4 µm M2 occupancy reservations.

**Compact pin escapes and MY.** NANY/NAND/NOR A and B share a column at
different y coordinates. The lower pin escapes downward, the upper upward.
Those mandatory M2 stubs and first channel landings, plus boundary-port
landings, are reserved before routing. Rows initially alternate R0/MY; annealing
also flips individual instances. This can share vertical pin-access columns
between rows while preserving supply polarity. All abstract constraints are
reflected with each cell. The selected adder contains both orientations.

**Floorplan and route capacity.** Automatic sizing enumerates physical row counts
and independently fed spans per row, including actual power-bank widths and
channel height in its area/aspect objective. It prefers aspect ≤1.5, then
minimum die area. Cell rows remain separated by horizontal routing channels.
Full_add/mac1/mul1 start with four tracks per channel; adder4 starts with eight.
Eight deterministic rip-up/reorder passes precede channel expansion by two
tracks (compact library). Only failed attempts add an extra side bypass track.
The selected four designs require no added side bypass tracks. The compact
NANY's three advertised full-height M2 tracks remain binding throughout.

**Placement.** Default effort is 600 annealing steps, seed 0. Swaps, moves and
MY flips minimize cell-terminal HPWL with a weak row-width penalty. Each
(row, span) has a hard current limit, every span has a fixed physical width,
and each span's aggregate current remains within the feed-bank envelope.
These constraints apply to the initial packing, every candidate and every
saved history frame. Cells are centered in their span on the 6 µm grid.
History HPWL is recomputed on the final routing-channel coordinates, so each
before/after pair compares identical floorplan dimensions. HPWL excludes
external ports; drawn wirelength includes their routes.

**Power / SIM compatibility.** Missing characterization uses 100 µA per logic
cell and zero intrinsic current for FILL/TIE. SIM's `max_static_current_a` and
`dc[*].rail_current_a` override defaults. The conservative 0.00025 A/µm width
scaling and immutable 4 µm lower cell rails previously limited adder4 to four
cells per row and forced sixteen rows. Internal vertical M2 banks now subdivide
long rows into independently fed spans. Adder4 uses eight physical rows with
two spans each and three banks (left/internal/right); the other designs need
only the two end banks. Each span still has the same two-ended current limit.
Internal banks are sized for half the aggregate load of each adjacent span;
an outer bank supplies half of its single neighboring span. The maximum
initial span load is reserved throughout annealing, so bank sizing stays valid.
Parallel unslotted trunks remain ≤42 µm. A 6.4 µm minimum trunk fits two V1
cuts at each 4 µm rail crossing; via arrays use the available rail/trunk widths.

SIM continues reading `build/<design>/<top>.pnr.json`. The `power.straps`,
`power.rails`, `power.vias`, `power.pins`, current maps, assumptions and
`ir_drop` records preserve their existing fields and units. Geometry lists
remain the authority for IR extraction. Additions are `feed_banks`,
`span_width`, `span_gap`, `span_current_limit_a`, and each strap's `bank` index;
`side` additionally accepts `internal`. Legacy trunk/stride fields describe
the outer banks only; internal banks can contain more parallel trunks.
Placements/history additionally carry `span`; `row` still means physical row.
No SIM source files or processes were changed. A file-based compatibility
check with SIM's existing `estimate_ir_drop` is retained separately as
`<design>.pnr.ir_compatibility.json`.

The PDK's local `openIP62/IP62/Technology/doc/OS00_リファレンスマニュアル_rev1.1.pdf`,
I.3.1/I.3.2, specifies M1(2 µm) 900 µA flat / 500 µA stepped, M2(3 µm) 3.7 mA,
and V1 780 µA/cut. Default `current_density_a_per_um=0.00025` uses the lower
stepped-M1 value with **assumed linear width scaling** for both metals; this is
not EM sign-off. Two-ended load sharing is a sizing approximation. PNR's IR
estimate assumes 0.05 Ω/square, groups parallel trunks at their mean x, and
omits via/package resistance. Divider zero shift uses equal pull-up/down
conductance for INV/NAND/NOR/BUF; NANY reports its VMID envelope. SIM's separate
geometry-based solver includes every drawn via and its assumed resistance.

**Verification.** Connectivity unions flattened drawn M1/V1/M2 islands and
checks every expected signal/power terminal and route. Direct-metal mock TIE
aliases are intentional; real RR ties retain separate metal nodes across their
resistor. Own routing DRC checks widths, spacing, wide-M1 spacing, fixed V1 cuts
and enclosure. The complete PDK deck runs without waived regions, disabled
warnings or skipped antenna rules; external TXM1/TXM2 labels are at the top
hierarchy because the deck reads top-cell labels for external gates. Official
report item counts, not process exit codes alone, determine DRC pass/fail.
An independent per-layer Region XOR of every used cell master in the archived
phase-2 and canonical phase-3 GDSs is empty for all four designs; area gains
come from the floorplan/routing changes with identical cell geometry.

Strict LVS compares the GDS against the GateNetlist plus `cells/out/all.spice`.
It establishes device/interconnect connectivity, not post-layout timing or
exhaustive transistor-level arithmetic correctness. Those remain SIM's scope.

## Reproduction and automatic updates

```
python3 examples/build_all.py
python3 examples/pnr_all.py
python3 examples/pnr_all.py --watch
```

The default designs are `adder4 full_add mac1 mul1`; default seeds are `0 7 19`.
Use `--force` to rebuild unchanged inputs, `--seeds ...`, `--anneal-steps ...`,
`--designs ...`, `--build-root ...`, or `--no-views` as needed. A missing shared
netlist invokes FRONTEND's build script. No git-state changes are performed.

The runner hashes the template, root publication/qualification files, every
published cell directory (including GDS/abstract/characterization/SPICE), the
four netlists and PNR/visualization/extraction entrypoint code. CELLS' independent
comparison scratch trees do not define a new cell publication; their final
root report does invalidate the cache. Watch mode polls every five seconds,
debounces changes, and reloads a changed publication. Every active build also
compares before/after fingerprints and restarts all designs if they differ.
Canonical results and seed evidence are hashed; missing/altered artifacts never
count as a cached pass. The actual batch observed publication changes and
restarted all four designs; the final run completed on a stable publication. The runner refreshes only the result-table block in this
status file for full canonical project builds. Custom/test builds leave it alone.

No watcher is running. `--watch` is an opt-in foreground script the integrator
can start and interrupt; a normal run exits after verification. Restart a watcher
after PNR Python implementation changes; cell/template/characterization
publications reload without restarting it. No watcher PID file is retained.

Each `build/<design>/` contains:

- `<design>.gds`, `.pnr.json`, `.pnr.summary.json`, `.seed_comparison.json`.
- `<design>.drc.lyrdb`, `.drc.log`, `.lvs.summary.json`; `lvs/` contains strict
  LVS databases, extracted SPICE, reference SPICE and the unmodified deck log.
- `pnr_seeds/seed{0,7,19}/` retains each candidate's physical and LVS evidence.
- `<design>.layout.png` and `.layout.html`, `.placement.html`, `.routing.html`.

## Public floorplan / placement controls

`place_and_route(..., rows=None, anneal_steps=600)` exposes the two notebook
controls. `rows=None` automatically sizes a near-square die; a positive integer
fixes its physical row count and adapts its power spans. `anneal_steps=0` keeps
initial placement, 600 is the fast default, and 2400 gives more optimization.
The CLI also accepts `--rows K --anneal-steps N`. Fixed rows can reduce
utilization; the API honors that explicit choice.

```python
from tritflow.pnr import place_and_route
from tritflow.viz.layout import placement_animation

r = place_and_route("build/adder4/adder4.json",
                    output_dir="build/adder4/notebook_rows10_steps2400",
                    rows=10, anneal_steps=2400, seed=7)
print(r.stats["die_size_um"], r.stats["utilization"], r.stats["runtime_s"])
placement_animation(r).show()
```

Controlled adder4 measurements (seed 7, same cells/netlist, every candidate
PDK-DRC clean and strict-LVS matched):

| Rows requested | Steps | Actual rows / spans | Die (µm) | Utilization | HPWL before → after (µm) | Signal length (µm) | PNR / +LVS (s) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Auto | 0 | 8 / 2 | 1752 × 1698 | 42.38% | 76903.5 → 76903.5 | 116083 | 8.70 / 9.61 |
| Auto | 600 | 8 / 2 | 1740 × 1590 | 45.57% | 74515.5 → 47968.5 | 79949 | 3.20 / 4.04 |
| Auto | 2400 | 8 / 2 | 1740 × 1590 | 45.57% | 74515.5 → 31296 | 65938 | 3.35 / 4.21 |
| 10 | 600 | 10 / 2 | 1518 × 1974 | 42.08% | 94653 → 52837.5 | 87766 | 3.70 / 4.67 |

Raw records and DRC/LVS evidence: `build/adder4/floorplan_comparison.json` and
`build/adder4/floorplan_comparison/`. Zero effort needed two more channel tracks;
its HPWL therefore uses those wider final channel coordinates for both frames.
All tested adder4 API runs finish below 10 s including strict LVS. Canonical
PNR timings below include library discovery, placement, routing, GDS export,
geometry checks and the PDK DRC. `+LVS` adds extraction/comparison; view rendering
is separate in each summary JSON. No phase-2 runtime was archived, so the
comparison makes no phase-2 speedup claim.

Canonical PNR + strict LVS + all four exported notebook views took adder4 12.50 s, full_add 4.51 s, mac1 5.87 s, mul1 2.68 s.
Timings are wall-clock measurements on this machine; concurrent stream/test
activity affects them. The slowest adder4 seed in the final batch is 6.90 s including LVS.

SIM compatibility checks on the canonical JSONs completed with every cell
connected to all three supply pads. Maximum rail deviations from SIM's
geometry-based solver are adder4 13.54 mV, full_add 7.27 mV, mac1 9.86 mV,
mul1 2.17 mV under its independent per-rail worst-current envelope.

## Notebook figures

```python
import json
from IPython.display import Image, display
from tritflow.viz.layout import (
    render_gds, layout_figure, placement_animation, routing_progress)

record = "build/adder4/adder4.pnr.json"
data = json.load(open(record))
display(Image(filename=str(render_gds("build/adder4/adder4.gds"))))
layout_figure(record, highlight_net="sum[0]",
              highlight_instance=data["placements"][0]["inst"],
              show_power=True).show()
placement_animation(record).show()
routing_progress(record).show()
```

The raster uses `klayout.lay.LayoutView` with the actual GDS hierarchy, correct
PDK drawing layers, hollow boundaries/well outlines, and an embedded legend.
It requires no display server and never modifies the GDS. The vector view has
working HTML net and instance dropdowns; instance hover shows cell type, source
hierarchy, orientation and physical dimensions. Wire thickness in this view is
schematic in pixels; use the GDS raster/JSON for physical metal widths.

Placement frames replay the actual saved positions with a linked HPWL cursor.
Routing frames replay the recorded order of the **successful routing pass**;
failed/ripped-up passes and widening attempts are retained in `routing_attempts`
instead of being presented as final-route geometry. Signal and supply routes
are separately identified in the record. `save_layout_views(result)` exports
all four artifacts beside a `PnrResult` in one call.

## Tests and dependencies

```
python3 -m pytest tests/pnr tests/viz/test_layout.py -q
python3 -m compileall -q tritflow/pnr tritflow/viz/layout.py examples/pnr_all.py
```

Final phase-3 combined run: **27 passed in 60.16 s** (concurrent with the final batch). This includes the original
synthetic suite and real four-trit adder, actual obstructed/mirrored mock GDS
through the full PDK deck, V1-implied metal, free-column metadata, alternative
pin access, portable raster/HTML, net/hierarchy selection, linked animation
frames, content changes with preserved mtimes, mid-build publication restart,
cache reuse, rebuilding a deleted checked GDS, and current/width/feed-envelope compliance of
every saved placement snapshot, plus the public row/annealing controls. A subsequent unchanged-input batch invocation
returned immediately with all checked artifacts current. `git diff --check`
and `compileall` on owned paths pass. The final actual GDS PNGs were visually
inspected, including the compact adder and mixed NAND/NOR/INV multiplier.

Extra packages installed: **none**. Uses existing klayout.db/lay 0.30.6, Plotly,
Pillow, numpy, matplotlib, the KLayout executable and the local PDK.

## Interface requests / ownership

No shared-contract changes requested. PNR JSON adds dimensions/hierarchy,
`routing_order`, `routing_progress`, corridor counts, library metadata and HPWL
statistics while preserving contracted placements/wires/vias/pins/power/history.
Own changes are confined to PNR paths, the explicitly assigned visualization
and test files, `examples/pnr_all.py`, and generated `build/` outputs.

<!-- PNR_RESULTS_BEGIN -->
## Current verified build results

Published template height: **132 µm**. Input content fingerprint: `d3a2eaa7dafec41abc1eacd0e0959d0f3b91611ae0957fc92cb9eae9324360cf`.

All outputs and reports are under `build/<design>/`. Utilization is placed cell area / die area; wirelength and signal via counts exclude the separately reported power geometry.

| Design | Seed | Die (µm) | Aspect | Utilization | M1 (µm) | M2 (µm) | Signal / power vias | PDK DRC | Strict LVS | PNR / +LVS (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---:|
| adder4 | 0 | 1740 × 1590 | 1.094 | 45.57% | 35778 | 41737.5 | 528 / 1152 | 0 violations | Match | 5.38 / 8.18 |
| full_add | 0 | 792 × 702 | 1.128 | 56.70% | 3924 | 6158.5 | 115 / 128 | 0 violations | Match | 2.11 / 4.15 |
| mac1 | 7 | 804 × 1038 | 1.291 | 51.44% | 7218 | 9730 | 172 / 288 | 0 violations | Match | 3.45 / 5.26 |
| mul1 | 0 | 372 × 366 | 1.016 | 52.35% | 750 | 1022.5 | 25 / 32 | 0 violations | Match | 1.30 / 2.54 |

## Phase 2 → phase 3

Before artifacts are preserved in each design's `phase2/`; cell library and input netlists are unchanged.

| Design | Die before → after (µm) | Aspect before → after | Utilization before → after | Die area reduction | Signal length before → after (µm) |
|---|---:|---:|---:|---:|---:|
| adder4 | 1176 × 3534 → 1740 × 1590 | 3.005 → 1.094 | 30.34% → 45.57% | 33.43% | 91254 → 77515.5 |
| full_add | 924 × 942 → 792 × 702 | 1.019 → 1.128 | 36.21% → 56.70% | 36.12% | 11817.5 → 10082.5 |
| mac1 | 912 × 1374 → 804 × 1038 | 1.507 → 1.291 | 34.26% → 51.44% | 33.40% | 17899.5 → 16948 |
| mul1 | 612 × 510 → 372 × 366 | 1.200 → 1.016 | 22.84% → 52.35% | 56.38% | 2106.5 → 1772.5 |

## Placement seed comparison

Cell-terminal HPWL excludes external ports. Each before/after pair uses the same final floorplan. Seed selection prefers aspect ≤1.5 and utilization ≥45%, then smallest die area and drawn signal wirelength; HPWL and seed break ties. All reported runtimes are measured on this machine, include PDK DRC, and exclude seed-search overhead.

| Design | Seed | HPWL before (µm) | HPWL after (µm) | Reduction | PNR / +LVS (s) | DRC / LVS |
|---|---:|---:|---:|---:|---:|---|
| adder4 | 0 | 74515.5 | 50436 | 32.31% | 4.88 / 6.35 | clean / Match |
| adder4 | 7 | 74515.5 | 47968.5 | 35.63% | 4.65 / 6.28 | clean / Match |
| adder4 | 19 | 74515.5 | 41388 | 44.46% | 5.12 / 6.90 | clean / Match |
| full_add | 0 | 6750 | 4752 | 29.60% | 6.12 / 8.36 | clean / Match |
| full_add | 7 | 6750 | 4617 | 31.60% | 3.15 / 5.06 | clean / Match |
| full_add | 19 | 6750 | 5115 | 24.22% | 3.34 / 5.04 | clean / Match |
| mac1 | 0 | 14685.5 | 6631.5 | 54.84% | 2.24 / 3.85 | clean / Match |
| mac1 | 7 | 14685.5 | 6723.5 | 54.22% | 2.40 / 4.75 | clean / Match |
| mac1 | 19 | 15501.5 | 8573.5 | 44.69% | 2.97 / 5.87 | clean / Match |
| mul1 | 0 | 1420.5 | 494.5 | 65.19% | 1.70 / 3.04 | clean / Match |
| mul1 | 7 | 1420.5 | 494.5 | 65.19% | 1.82 / 3.27 | clean / Match |
| mul1 | 19 | 1420.5 | 588.5 | 58.57% | 1.38 / 3.03 | clean / Match |

Machine-readable results: `build/pnr_summary.json`, `build/pnr_manifest.json`, and each design's `.pnr.summary.json` / `.seed_comparison.json`.
<!-- PNR_RESULTS_END -->
