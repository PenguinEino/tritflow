# PNR stream — phase 2

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

Final content-hash verification and status publication are running. No circuit
or routing blocker remains; all four designs and all twelve seeds have passed.

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

**Compact pin escapes.** NANY/NAND/NOR A and B share a column at different y
coordinates. The lower pin must escape downward and the upper pin upward.
These mandatory M2 stubs and their first channel landing, plus boundary-port
landings, are reserved before maze routing other nets. This removed a full-
adder routing failure that horizontal widening alone had inflated to 73 tracks;
the compact full-adder now routes in 12-track channels.

**Vertical capacity.** The compact NANY exposes only three full-height free M2
columns, two of which carry signal terminals. Horizontal-channel widening
cannot repair a lack of vertical transit capacity. Compact builds therefore
reserve eight additional vertical signal tracks per side between the cell rows
and power banks. Routing failure grows both the horizontal channels and these
vertical corridors. This is an explicit die-area cost, included in utilization,
wirelength and HPWL measurements. Cell metal is never removed or ignored.

**Placement metric.** Saved HPWL is computed from actual selected cell signal
accesses, excluding external ports. Initial and final snapshots are evaluated
in the same final floorplan, including any channel expansion. Width/height and
source `hier` are embedded in each placement and history snapshot. The selected
seed minimizes final HPWL among candidates that pass complete routing, own
checks, PDK DRC and strict LVS; total signal wirelength and seed break ties.
Different seeds can require different row counts or channel widths, so their
initial HPWL values need not be identical. The tables retain those differences.

**Power.** Missing characterization uses 100 µA per logic cell and zero intrinsic
current for FILL/TIE. SIM's `max_static_current_a` and `dc[*].rail_current_a`
override defaults. Sizing sums cell maxima; rail IR uses independently maximized
per-rail currents, a conservative envelope rather than one realizable vector.
Both row ends feed separate VDD/VMID/VSS M2 banks. Individual unslotted trunks
remain at most 42 µm and are split when more total width is required. The compact
4 µm lower rails and assumed current limit can require extra cell rows.

The PDK's local `openIP62/IP62/Technology/doc/OS00_リファレンスマニュアル_rev1.1.pdf`,
I.3.1/I.3.2, specifies M1(2 µm) 900 µA flat / 500 µA stepped, M2(3 µm) 3.7 mA,
and V1 780 µA/cut. Default `current_density_a_per_um=0.00025` uses the lower
stepped-M1 value with **assumed linear width scaling** for both metals; this is
not EM sign-off. The IR estimate assumes 0.05 Ω/square, groups parallel trunks
at their mean x, and omits via/package resistance. Divider zero shift uses equal
pull-up/down conductance for INV/NAND/NOR/BUF; NANY reports its VMID envelope.

**Verification.** Connectivity unions flattened drawn M1/V1/M2 islands and
checks every expected signal/power terminal and route. Direct-metal mock TIE
aliases are intentional; real RR ties retain separate metal nodes across their
resistor. Own routing DRC checks widths, spacing, wide-M1 spacing, fixed V1 cuts
and enclosure. The complete PDK deck runs without waived regions, disabled
warnings or skipped antenna rules; external TXM1/TXM2 labels are at the top
hierarchy because the deck reads top-cell labels for external gates. Official
report item counts, not process exit codes alone, determine DRC pass/fail.

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
count as a cached pass. The runner refreshes only the result-table block in this
status file for full canonical project builds. Custom/test builds leave it alone.

Each `build/<design>/` contains:

- `<design>.gds`, `.pnr.json`, `.pnr.summary.json`, `.seed_comparison.json`.
- `<design>.drc.lyrdb`, `.drc.log`, `.lvs.summary.json`; `lvs/` contains strict
  LVS databases, extracted SPICE, reference SPICE and the unmodified deck log.
- `pnr_seeds/seed{0,7,19}/` retains each candidate's physical and LVS evidence.
- `<design>.layout.png` and `.layout.html`, `.placement.html`, `.routing.html`.

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

Latest combined run: **25 passed in 48.51 s**. This includes the original
synthetic suite and real four-trit adder, actual obstructed/mirrored mock GDS
through the full PDK deck, V1-implied metal, free-column metadata, alternative
pin access, portable raster/HTML, net/hierarchy selection, linked animation
frames, content changes with preserved mtimes, mid-build publication restart,
cache reuse and rebuilding a deleted checked GDS. A final rerun after the batch
reporting adjustment is in progress. `git diff --check` on owned paths passes.

Extra packages installed: **none**. Uses existing klayout.db/lay 0.30.6, Plotly,
Pillow, numpy, matplotlib, the KLayout executable and the local PDK.

## Interface requests / ownership

No shared-contract changes requested. PNR JSON adds dimensions/hierarchy,
`routing_order`, `routing_progress`, corridor counts, library metadata and HPWL
statistics while preserving contracted placements/wires/vias/pins/power/history.
Own changes are confined to PNR paths, the explicitly assigned visualization
and test files, `examples/pnr_all.py`, and generated `build/` outputs.

<!-- PNR_RESULTS_BEGIN -->
Current tables are being published by the final content-aware batch run.
<!-- PNR_RESULTS_END -->
