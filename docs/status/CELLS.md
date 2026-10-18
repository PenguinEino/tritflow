# CELLS — Phase 5 complete; compact library and notebook cell visuals qualified

## Published generation

The live library is generation `2026-10-18T08:40:04.261111+00:00` (Phase 4 evidence; physical views unchanged from `2026-10-18T07:47:24.187502+00:00`). All nine cells now use
**132 um** common height and a **6 um** routing grid. The PNR library loader
accepts every view. The tall generation remains in integrator tag `cells-v1-tall`.

The publish exchanged the whole output directory atomically, including GDS,
schematic/LVS references, extraction, abstracts, truth tables, PNGs, fresh SIM
characterization and verification. `cells/template.json` now links to
`out/template.json`, so template and cell views change together. Live rebuilds
stage privately, qualify/characterize all nine cells, then use the same exchange.
Focused builds require `--out` and do not modify the live library. Readers needing
a multi-file snapshot can compare `generation.json` before/after reading.

## Compact geometry

| Cell | New width x height (um) | Original area (um2) | New / original | Free full-height M2 tracks |
|---|---:|---:|---:|---:|
| INV | 108 x 132 | 6,336 | 2.25 | 13 |
| NAND | 144 x 132 | 16,632 | 1.14 | 6 |
| NOR | 144 x 132 | 16,632 | 1.14 | 6 |
| NANY | 168 x 132 | 17,020 | 1.30 | 3 |
| BUF | 216 x 132 | 12,672 (two INV) | 2.25 | 25 |
| TIEP | 72 x 132 | new support cell | — | 9 |
| TIEZ / TIEN | 72 x 132 | new support cell | — | 8 |
| FILL | 24 x 132 | new support cell | — | 2 |

The INV/BUF 2.25 ratio reflects NANY's common row height and 6 um side access
margins. They are close to the approximate 2x goal; the other source gates are
comfortably below it. INV area decreased 91.4% and NANY 92.9% from the tall
version. No hundreds-of-micrometre poly bus remains.

Device placement/local wiring comes from copied geometry in the taped-out
`build_inverter.py`, `build_nany.py`, `build_mul_primitives.py`, with no imports
from or changes to that repository. INV/NANY keep their original placements.
NAND/NOR's PMOS row moves down 8 um and upper RR down 6 um. All MOS dimensions,
RR W/L=2.8/30 um, bulk nets, resistor substrates and guard ties are preserved.
BUF is two adapted INV placements. Children carry macro suffixes, preventing
PCell variant collisions when GDS files merge.

Rails: VDD y=124–132 (8 um), VMID y=6–10 (4 um), VSS y=0–4 (4 um), all M1
and full width. The original local VSS stripe is retained at y=12–15.4 and
connected across VMID using a short M2 bridge. The nwell band y=116–132 is
continuous across abutments and tapped in each macro. RR wells stay separate.
These local rail widths are not permission to feed arbitrary-length rows from
one end; PNR must retain current-based power feeds/straps.

M2/V1 crossovers are now allowed per the Phase 3 override. Abstracts contain
exact rectangle decompositions of M1, M2 and V1, with free full-height M2 track
coordinates/counts computed for 3.4 um wire width and 2 um clearance. Public
pins are M1, with 3.4 um pads and x=6k+3 access. Signal pins are on edge columns
that permit vertical escape without colliding with internal M2.

Ties retain the finite-drive RR30 structure (selected rail to Y; well/guard at
VDD). FILL is device-free with rails, well continuity and body taps. Its PDK
standalone LVS mismatch caused by `netlist.purge` is retained. Qualification
requires empty extraction, exact rail/well coverage, and strict three-rail RR
probe-fixture LVS. No dummy devices, warnings disabled, or waiver layers.

## Phase 3 validation

- All nine drawings: zero official PDK drawing DRC markers.
- All 324 ordered-pair/R0/MY abutment cases: zero markers.
- Eight electrical cells: strict official LVS match, no extraction errors.
- FILL: empty extraction, coverage, and four matching probe-fixture circuit pairs.
- All 36 nominal extracted DC points pass; max error 0.158936 V (NOR A=B=0).
- Fresh SIM characterization at 10 fF, 100 fF, 1 pF passes for all electrical cells;
  each `.char.json` source hash matches its newly published `.ext.spice`.
- Compact phase-1 regression: 7 passed in 28.94 s, including every advertised
  pin landing with real PDK vias/M2 pads, both orientations, DRC checked.

The quick DC solver now seeds Y with its ideal initial guess. This is a `.nodeset`,
not a forced IC: unseeded NOR occasionally converged to a nonphysical ~526 V
root even though source and generated networks LVS-match. Phase 2 additionally
uses connectivity-derived internal-node initial guesses, as the original checks do.

## Phase 2 device-level identity only

**The table below proves device-level identity only.** Neither extraction contains
interconnect parasitics. Identical numbers therefore do not establish physical
layout performance equivalence or show the effect of compaction on wire delay.

`cells/out/equivalence_report.json` now reports **passed** for five electrical
circuits and all four cascade protocols. INV/NAND/NOR/NANY are compared against
fresh PDK extraction of their actual taped-out GDS and freshly netlisted Xschem
schematics. BUF is compared against two copies of the independent INV schematic
and extracted circuit. Both original and compact GDS strictly match those source
references. Device sizes, connectivity and intrinsic junction parameters agree.

Nominal 27 C; ideal +5/0/-5 V supplies. The following values are original / compact.
Static current is the maximum absolute rail current across all DC states.
Settling is from input-edge start to permanent entry in the +/-0.5 V band.
Last digits can differ from quick DC/full-characterization tables because of
Newton initialization/tolerances; every original/compact pair uses the same bench.

| Cell | Worst DC error (mV), original / compact | Static current (uA), original / compact | Worst settling at 10 fF (ns), original / compact |
|---|---:|---:|---:|
| INV | 39.537 / 39.537 | 407.165 / 407.165 | 4.270 / 4.270 |
| NAND | 102.597 / 102.597 | 435.377 / 435.377 | 8.947 / 8.947 |
| NOR | 158.904 / 158.904 | 434.204 / 434.204 | 21.238 / 21.238 |
| NANY | 44.640 / 44.640 | 421.373 / 421.373 | 16.887 / 16.887 |
| BUF | 35.233 / 35.233 | 814.301 / 814.301 | 7.283 / 7.283 |

All DC grids pass: 81 points for INV/BUF, 81x81 for each two-input gate,
with the original +/-0.5 V input neighborhoods checked. All 6/72 directed
input transitions pass at both 10 fF and 100 fF, with 100 ns holds, 1 ns edges
and 0.1 ns max steps. NANY also passes all 72 transitions with either A or B
delayed 2 ns. Maximum original/compact grid difference is 7.62e-14 V;
static-current differences are zero and transition settling differences are
below 1.7e-21 s in this run. Those tiny differences are numerical.

| Cascade protocol | Worst sampled output error (mV), original / compact | Status |
|---|---:|---|
| inverter_two | 39.537 / 39.537 | Both pass |
| nor_six | 215.532 / 215.532 | Both pass |
| nany_six | 122.452 / 122.452 | Both pass |
| mixed_six | 158.455 / 158.455 | Both pass |

The two-INV protocol retains the original 20 ns holds; the six-stage NOR
(A-driven, B-driven, tied-input), added six-stage NANY in the same three modes,
and mixed INV/NAND/NOR/NANY/INV/NANY paths use 200 ns holds, include all stages
and the original +/-1, +/-0.5, +/-0.2 V near-zero perturbations. Cascade DC
sweeps and all transient checkpoints pass. Maximum cascade DC difference is
2.02e-12 V. Historical RR20 TB snapshots are not reused as circuit definitions;
fresh RR30 source circuits are used with the original stimulus/check protocols.

The extra six-NANY tied-input cascade initially found the same nonphysical
BSIM root in both versions. `equivalence_report.unseeded.json` and diagnostic
decks/logs retain that failure. A generic MOS-polarity guess mis-initialized
RR endpoints behind off MOS stacks. The homogeneous six-NANY protocol seeds each stage from separately solved,
bounded single-cell DC operating points. The original mixed-chain protocol
retains its original connectivity-derived guesses; applying the homogeneous
initialization there also reached a common nonphysical root, now retained under
`equivalence/mixed_overseeded_diagnostic`. These are
Newton `.nodeset` guesses, not forced `.ic`/`uic` values or circuit changes.
The refined test passes in both networks, including all tied-input stages.
A separate Gear-2 diagnostic also passes; the reported comparison retains
the default trapezoidal method.

Runnable decks, logs, unmodified reference extraction and compressed DC/cascade
data are retained under `cells/out/equivalence/`. The final report includes source,
GDS, extraction and model SHA256 provenance. Ties/FILL are new support cells
with no taped-out counterpart and retain their phase-1 checks.

**Scope:** intrinsic device/junction extraction only. Interconnect R/C,
PVT/mismatch, pad/package effects and manufacturing signoff are not covered.
The intrinsic parameters are identical and interconnect parasitics are absent
in both models, so these results do not measure layout-dependent wire delay.

## Commands / dependencies

`python3 -m tritflow.cells build` privately builds, qualifies, characterizes and
publishes a complete generation. `verify` runs phase-1 checks; `equivalence`
runs phase 2 against `~/balanced-ternary-logic`. `--out` selects a private stage.
`python3 -m pytest tests/cells -q` includes the ported Phase 2 checks. Final
run: **16 passed in 504.21 s (8:24)**, against an independently rebuilt private
compact library. All published GDS/extraction/abstract verification hashes were
rechecked after this run and still match. Phase 4 final run: **24 passed in
492.89 s (8:12)**, including the new estimated-wire-C and poly checks. The full
five-cell/four-cascade wire-C comparison also passed. No CELLS blockers remain.

No extra packages installed. No reference or PDK files changed. Only owned paths
were edited. No git-state-changing commands were run.

## Interface requests

None. Consume final template/abstracts; retain the FILL method. Distinguish the
Phase 2 device-only identity proof from Phase 4 estimated-metal-C results; neither
models poly R/C or full calibrated PEX. W/L DC sizing belongs to SIM. Generation
IDs support snapshot checks.

## Publish journal

Publish 2026-10-18T07:47:24.187502+00:00: Phase 3 compact cells, 132 um common height; phase-1 checks and fresh full characterization passed. Whole-library directory exchange; height 132 um. GDS/SPICE/extraction/abstracts/truth/PNG/characterization/verification and template belong to this generation.

Evidence publish 2026-10-18T08:07:34.359407+00:00: five-cell original/compact equivalence and four cascade protocols PASS; cell-view generation remains 2026-10-18T07:47:24.187502+00:00. Failed unseeded diagnostics retained.

Final verification 2026-10-18T08:22:49.239261+00:00: 16 CELLS tests passed; published phase-1 and phase-2 reports both passed; live input hashes unchanged.

## Phase 4 — estimated wire C and poly resistance

The previous Phase 2 results establish **device-level identity only**, not
layout performance equivalence: both networks omit all interconnect parasitics.
The new comparison stages a full copy of the live generation, measures connected
M1/M2 polygons in the actual original and compact GDS with SIM's public
`gds_wire_capacitance`, maps corresponding nets through the independent schematic
LVS cross-reference, and calls `append_wire_capacitance` on both extracted models.
Annotated models, per-net geometry/C and runnable benches are retained separately;
LVS `.ext.spice`, GDS and existing characterization remain unchanged.

SIM's assumptions are epsilon_r=3.9, effective metal heights M1/M2=1/2 um,
area C=0.03453/0.01727 fF/um2 and fringe=0.02 fF/um perimeter. This is estimated
lumped substrate C, **not calibrated/signoff PEX**. Coupling, shielding, via C,
poly C and wire R are absent. Unconnected/purged metal is explicitly reported
by the API. BUF's original reference is two original INV macros with an ideal
connection, not a fabricated BUF layout; no original inter-macro route is invented.
The same DC grids/current checks, 10/100 fF transitions, NANY skew cases and four
cascade protocols were repeated and all passed in both layouts. Functional bands and hold times remain
unchanged; geometry-dependent timing differences are measured, not forced to zero.

### W/L sweep ownership decision

FRONTEND's exact proposal in `docs/status/FRONTEND.md` requests
`tritflow.sim.sizing.sweep_dimensions(cell, candidates, *, sweep_pin="A",
fixed_trits=None, start_v=-5.0, stop_v=5.0, step_v=0.1, temperature_c=27.0,
pdk=None, workdir=None, timeout=120.0)`.
It explicitly creates temporary source-level SPICE variants for nominal DC
experiments and never generates/qualifies layout or mutates published extracts.
This is pure simulation and belongs to **SIM**. CELLS already supplies the
canonical device IDs and adopted dimensions through `circuits()`/published source.
SIM's current `tritflow/sim/sizing.py` now contains the requested entrypoint;
CELLS does not duplicate or edit it. No cell-generation sizing API is needed.

### Long-poly resistance assessment

The installed PDK supplies no calibrated sheet resistance for gate/interconnect
GC (8/1). `models_IP62_res_v5.lib` uses 95*magRS ohm/square for resistor poly
GR (8/2); `models_IP62_mos_v2.lib` has MOS diffusion `rsh=44.9607`. Neither
represents GC, so neither is substituted for it. The documented GC assumption is
**20 ohm/square**, with sensitivity **5–100 ohm/square**. No poly resistance is
inserted into the capacitance-only comparisons.

The inventory uses actual LVS-connected GC polygons, removes active regions and
contact cuts, and decomposes straight field-poly rectangles at bends/widenings.
It lists every section at least 10 um long and at most 3 um wide, with its net,
bounding box, L/W and R=Rsheet*L/W in `parasitic_aware.poly_resistance`.
These are straight-segment estimates, not solved end-to-end gate resistances.
The longest signal sections (all 1 um wide) are:

| Cell | Longest field-poly section, original / compact (um) | Estimated segment R, original / compact (ohm) |
|---|---:|---:|
| INV | 10.95 / 10.95 | 219 / 219 |
| NAND | 39.20 / 31.20 | 784 / 624 |
| NOR | 31.45 / 31.45 | 629 / 629 |
| NANY | 30.20 / 30.20 | 604 / 604 |
| BUF | 10.95 / 10.95 | 219 / 219 |

NAND's upper gate runs are 8 um shorter; NOR's upper runs also shorten by 8 um,
while its longest lower B run is retained. INV/NANY signal poly is inherited
without lengthening. BUF contains two INV copies. RR guard-ring sections on VDD
include 41x2 um rectangles (410 ohm under the assumption); these are distinguished
from signal gate buses in the inventory. The worst compact signal section is
629 ohm nominal, or 157–3145 ohm across the assumed sheet-R range. Gate charging
through these distributed resistances remains a timing concern. Metal-C checks
cannot validate that effect; calibrated GC/contact R and poly C are needed for
that claim. This limitation also applies to the original layout.

### Parasitic-aware results

All five cell comparisons and all four cascade protocols **pass** at the
original functional limits. DC-grid differences are at most 7.62e-14 V; static
current differences are zero. C is open at DC, so that agreement is expected.
The following settling times include the estimated metal C plus the stated
external load. Supplies are ideal; added rail C does not model IR drop or bounce.

| Cell | DC error original / compact (mV) | Static current original / compact (uA) | Worst settling at 10 fF original / compact (ns) |
|---|---:|---:|---:|
| INV | 39.537 / 39.537 | 407.165 / 407.165 | 4.724 / 4.759 |
| NAND | 102.597 / 102.597 | 435.377 / 435.377 | 10.039 / 10.053 |
| NOR | 158.904 / 158.904 | 434.204 / 434.204 | 22.690 / 22.626 |
| NANY | 44.640 / 44.640 | 421.373 / 421.373 | 19.465 / 19.556 |
| BUF | 35.233 / 35.233 | 814.301 / 814.301 | 7.991 / 8.121 |

NOR's slightly faster compact worst-case settling is consistent with its
PMOS-side NET2 capacitance dropping by 1.557 fF; Y gains 0.709 fF. Rail
extensions primarily load ideal supplies. NAND
also loses 2.466 fF on NET1 while gaining 0.709 fF on Y. Most internal signal
geometry is inherited unchanged. BUF gains 5.119 fF on its midpoint connection.
The largest paired transition difference across all cell protocols is 0.557 ns
(NANY, B delayed 2 ns); this differs from subtracting the two worst-case times
because the worst transition can differ. All 10/100 fF and both skew suites pass.

| Cascade | Worst sampled error original / compact (mV) | Worst settling across all stages original / compact (ns) | Maximum paired settling difference (ns) |
|---|---:|---:|---:|
| inverter_two | 39.537 / 39.537 | 8.049 / 8.135 | 0.092 |
| nor_six | 215.532 / 215.532 | 74.078 / 74.085 | 0.226 |
| nany_six | 122.452 / 122.452 | 113.857 / 114.318 | 0.461 |
| mixed_six | 158.455 / 158.455 | 64.662 / 64.875 | 0.213 |

Cascade DC curves agree within 2.02e-12 V. All stages meet the original
20 ns (two INV) / 200 ns (six-stage) hold-time checks, including near-zero
perturbations. These results support nominal functional agreement under the
stated **estimated metal-C model only**, not full interconnect-RC equivalence.

### Per-net estimated capacitance

Values below are fF; full-precision C, per-layer merged area/perimeter,
coefficient/API/source hashes and extracted-node correspondence are in
`equivalence_report.json` → `parasitic_aware.per_net_capacitance` and
`capacitance_details`. Net names come from the independently matched schematic,
not the unrelated anonymous extraction numbers. Unloaded VMID metal purged
from INV/NAND/NOR/BUF extraction is excluded; omitted area is reported explicitly
by the API. The table lists every retained connected net.

| Cell | Schematic net | Original C (fF) | Compact C (fF) |
|---|---|---:|---:|
| INV | A | 1.986 | 3.221 |
| INV | NET1 | 6.368 | 6.368 |
| INV | NET2 | 7.536 | 7.536 |
| INV | VDD | 25.798 | 66.137 |
| INV | VSS | 18.465 | 41.378 |
| INV | Y | 4.543 | 6.030 |
| NAND | A | 3.651 | 5.139 |
| NAND | B | 5.132 | 6.619 |
| NAND | NET1 | 23.432 | 20.966 |
| NAND | NET2 | 13.277 | 13.277 |
| NAND | NET3 | 4.465 | 4.465 |
| NAND | VDD | 53.511 | 78.089 |
| NAND | VSS | 26.662 | 55.987 |
| NAND | Y | 8.515 | 9.223 |
| NOR | A | 3.651 | 5.139 |
| NOR | B | 5.132 | 6.619 |
| NOR | NET1 | 10.694 | 10.694 |
| NOR | NET2 | 17.189 | 15.632 |
| NOR | NET3 | 14.678 | 14.678 |
| NOR | VDD | 49.770 | 74.738 |
| NOR | VSS | 28.418 | 57.742 |
| NOR | Y | 8.515 | 9.223 |
| NANY | A | 19.128 | 20.615 |
| NANY | B | 15.885 | 17.372 |
| NANY | NET1 | 9.656 | 9.656 |
| NANY | NET2 | 17.347 | 17.347 |
| NANY | NET3 | 15.291 | 15.291 |
| NANY | NET4 | 3.945 | 3.945 |
| NANY | NET5 | 13.524 | 13.524 |
| NANY | NET6 | 13.524 | 13.524 |
| NANY | VDD | 50.096 | 82.173 |
| NANY | VMID | 18.008 | 50.966 |
| NANY | VSS | 30.258 | 65.117 |
| NANY | Y | 28.933 | 31.680 |
| BUF | A | 1.986 | 3.221 |
| BUF | MID | 6.529 | 11.648 |
| BUF | STAGE0_NET1 | 6.368 | 6.368 |
| BUF | STAGE0_NET2 | 7.536 | 7.536 |
| BUF | STAGE1_NET1 | 6.368 | 6.368 |
| BUF | STAGE1_NET2 | 7.536 | 7.536 |
| BUF | VDD | 51.595 | 131.955 |
| BUF | VSS | 36.930 | 80.832 |
| BUF | Y | 4.543 | 6.030 |

Annotated original/compact models and per-net geometry are retained under
`cells/out/equivalence/parasitic/<CELL>/`; all DC/settling/cascade decks and
logs are below that comparison tree. Public `.ext.spice` remains the clean
device-only LVS view. `python3 -m tritflow.cells parasitic` reproduces Phase 4
in a private full-library snapshot and atomically publishes the evidence.

Publish 2026-10-18T08:40:04.261111+00:00: Phase 4 original/compact estimated wire-C comparison PASS for five cells and four cascades; 24 CELLS tests passed; physical cell views unchanged. Whole-library directory exchange; height 132 um. GDS/SPICE/extraction/abstracts/truth/PNG/characterization/verification and template belong to this generation.

Final Phase 4 validation 2026-10-18T08:40:04.374013+00:00: **24 tests passed**;
all five estimated-wire-C cell comparisons and four cascades passed. Published
via whole-directory atomic exchange. All nine cells' GDS/SPICE/extraction/abstract/
truth/PNG hashes match the prior generation; latest live SIM characterizations
and sizing artifacts were preserved. No SIM/extract code or PDK/reference files
were edited. No extra dependencies or git-state changes.

## Phase 5 — chapter 3 cell visuals

New ownership: `tritflow/viz/cell.py` and `tests/viz/test_cell*.py`. The views read
only published `cells/out` data. Layer polygons are taken from GDS with hole-safe
trapezoid decomposition, not drawn from schematic guesses. Device placement is
joined through persisted strict LVS device pairs to canonical published SPICE;
optional original XM/R labels come from the independent LVS evidence already
inside `cells/out`. Actual GDS active-region bounds outline each MOS/RR device.
The linked device table uses standalone HTML/Plotly JavaScript, so ipywidgets and
anywidget are not runtime requirements. Separate ordinary Figure/table objects
remain available for static notebook use. No cell outputs were modified.

### Notebook API

Import directly from `tritflow.viz.cell` (no changes to shared viz exports):

```python
from IPython.display import display
from tritflow.viz.cell import (
    cell_figure, device_mapping, device_locations, device_table, row_abutment,
)

display(cell_figure("NANY", theme="dark"))
view = device_mapping("NANY", theme="light")
display(view)                       # linked Plotly + clickable device table
view.select("XM9")                 # original alias, or published ID "XCN2"
display(view.figure, view.table)    # ordinary figures; no widget/HTML coupling
view.write_html("nany-devices.html")  # standalone, Plotly bundled by default

display(row_abutment(
    ["INV", "NAND", "NANY", "BUF", "FILL"],
    orientations=["R0", "MY", "R0", "MY", "R0"],
    theme="light",
))
rows = device_locations("INV")     # JSON-ready name/alias/model/W/L/origin/bbox
static_table = device_table("INV")
```

- `cell_figure(cell, *, library=CELLS_DIR/"out", theme="light") -> go.Figure`:
  actual WN/AP/AN/AR/GC/CO/M1/V1/M2 polygons, independent layer legend groups,
  dashed exact M2/V1 router obstructions, signal access pads/labels, cell boundary
  and labelled VDD/VMID/VSS M1 rail overlays. Legend single-click toggles a group;
  double-click isolates one. Both light/dark palettes use explicit backgrounds
  and contrasting text. Axes retain physical 1:1 scale and µm units.
- `device_locations(cell, *, library=...) -> list[dict]`: one row per actual
  schematic device, with unique published SPICE `name`, original
  `schematic_name` when available, `model`, `w_um`, `l_um`, `x_um`, `y_um`, and
  `bbox_um`. Coordinates are the matched extraction/PCell origins; boxes enclose
  actual active geometry, including RR end regions (not an inferred W×L box).
  FILL returns an empty list; taps/vias are correctly excluded. BUF aliases are
  stage-qualified, so its eight devices remain distinct. Missing independent
  evidence falls back to published names/PCell roles without any reference-repo
  access. The main persisted cell LVS pairs and source dimensions must agree.
- `device_mapping(cell, *, library=..., theme="light", selected=None)` returns
  `DeviceMapping`: `.figure`, `.table`, `.rows`, `.select(name_or_alias_or_None)`,
  `.static_figures()`, `.to_html(full_html=True, include_plotlyjs=True)` and
  `.write_html(path, include_plotlyjs=True)`. Device outlines/labels are all
  visible; hovering an outline shows schematic and SPICE names, model, W/L and
  origin. The linked table supports whole-row clicks and keyboard Tab/Enter/Space.
  Selection updates both the outline and native figure dropdown; clicking an
  outline also selects its table row. `.figure` and `.table` are ordinary Plotly
  figures, and the figure dropdown works without a Python callback. For notebook
  hosts that restrict HTML/iframes, display those two attributes or the tuple
  from `.static_figures()` instead. No FigureWidget/ipywidgets/anywidget required.
- `device_table(cell, *, library=..., theme="light") -> go.Figure`: separate
  Plotly table of schematic label, published ID, model, W/L and GDS origin.
- `row_abutment(cells=("INV","NAND","NOR","NANY","FILL"), *,
  orientations=None, library=..., theme="light") -> go.Figure`: actual transformed
  cell polygons side by side. Default orientations alternate R0/MY; only those
  orientations are accepted. It checks aligned heights/rails and physical M1
  coverage before claiming continuity. Per-cell labels and hover expose the
  advertised free full-height M2 tracks/count, width and clearance; MY mirrors
  geometry, pins and tracks. These centerlines are the abstract's routing-space
  promise, not a fabricated routing result. Free-track and rail legend entries
  appear first in the row view.

All functions accept INV/NAND/NOR/NANY/BUF/TIEP/TIEZ/TIEN/FILL, validate names and
light/dark themes, and check `generation.json` before/after multi-file reads.
Figures never write to the library. The optional HTML export writes only to the
caller-specified destination; its default includes Plotly locally, with no CDN.

### Phase 5 validation / publication

`python3 -m pytest tests/viz -q`: **56 passed**, including **33 cell-visualization
cases**. Coverage includes all nine cells in both themes; rendered GDS polygon
and obstruction equality (including holes); every source device's matched
location/dimensions/outline/table entry; original XM/R aliases and BUF hierarchy;
selection/export/static fallback; portable data without PDK/reference/equivalence
trees; mirrored tracks/pins, continuous rails and publication-change rejection.

Chrome review confirmed light/dark NANY geometry, row-abutment geometry, table
click and keyboard selection with the corresponding highlighted device, and the
notebook iframe representation (including Unicode labels and selection). An
initial overlapping dropdown/title and an unspecified-host-charset issue were
corrected before the final test run.

Phase 5 is complete. **No `cells/out` publish was needed or performed**: this
phase changes visualization code/tests/status only; all physical cell views,
characterizations and existing equivalence evidence remain as published. No
shared notebook/viz exports, PNR/SIM code, PDK/reference files or git state were
modified. No extra dependencies were installed. No blockers/interface requests.

## Phase 6 — STA timing tables (in progress; schema contract)

Producing `cells/out/<CELL>/<CELL>.timing.json` for all nine cells. Proposed schema
is fixed here early for STA to implement against; publication will be atomic.

- `schema_version: 1`, `cell`, `inputs: [pin,...]`, `output: "Y"` (null for FILL),
  `source_sha256` (the clean `.ext.spice`), model/code provenance, `generation`,
  `complete`, `passed`, `kind: "logic" | "constant" | "physical"`.
- `axes: {load_f: [5e-15,1e-14,2e-14,5e-14,1e-13,2e-13,5e-13,1e-12],
  input_transition_s: [1e-9,1e-8,5e-8,1.5e-7]}`. Input transition is the full
  0–100% linear voltage ramp, not 10–90% slew or a binary threshold delay.
- `arcs: [...]`: **one arc per directed single-input transition with every other
  input fixed at a specified trit**. Fields: `id`, `input_pin`, `output_pin`,
  `input_from`, `input_to`, `output_from`, `output_to`, `from_inputs`, `to_inputs`,
  `side_inputs`, `changed_inputs`, and matrices `settling_s`, `output_slew_10_90_s`,
  `passed`, `status`, `error_v`. Matrix order is **[input-transition index][load
  index]**. `side_inputs` is the sensitizing constant-input assignment, preserving
  the ternary function/correlation rather than merging incompatible arcs.
- `simultaneous: [...]` holds the remaining multi-input vector changes, with the
  same matrices and `input_pin: null`; these are synchronous-ramp observations,
  not single-pin propagation arcs. Complete directed coverage: 6 vector changes
  for INV/BUF; 72 for NAND/NOR/NANY (36 single-pin, 36 multi-pin). Unchanged-output
  arcs are retained (including any measured hazard recovery), not discarded.
- `settling_s` is measured from **input edge START** to final entry in the new
  ideal output's ±0.5 V band, remaining there through the recorded observation
  window. Null means unsettled or solver failure; consult `status` and `passed`.
  Never interpolate through null/failed entries or silently extrapolate beyond
  either tested axis. Outputs with no level change have null 10–90% slew.
- `input_capacitance: {method, frequency_hz, rows, per_pin}`: fresh SIM biased
  small-signal AC driving-point C at 1 MHz, unloaded output, every discrete input
  bias. `rows` use SIM's `{input_trits, pin, capacitance_f}` schema; `per_pin` maps
  each input to `{min_f,max_f}`. Use `max_f` for a bias-independent fanout bound.
- TIEP/TIEZ/TIEN have `kind:"constant"`, no input arcs, empty capacitance rows,
  and `constant_trit`; FILL has `kind:"physical"`, no output/arcs/capacitance.

The primary table uses the **device-only extracted model**, matching existing
`.char.json` and SIM's post-layout device network. It does not add the cell's
metal C to input capacitance and then count that same metal again in PNR GDS
wire C. STA may add its separately estimated net wire C. Poly-R augmentation and
its measured sensitivity will be reported separately rather than silently
changing the structural LVS extraction or claiming unverified calibrated GC R.
SIM's IP62 parameter audit is being monitored for the published poly values.
