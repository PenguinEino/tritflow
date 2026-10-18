# CELLS — Phase 3 and Phase 2 complete

## Published generation

The live library is generation `2026-10-18T07:47:24.187502+00:00`. All nine cells now use
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

## Phase 2 equivalence

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
rechecked after this run and still match. No outstanding CELLS work or blockers.

No extra packages installed. No reference or PDK files changed. Only owned paths
were edited. No git-state-changing commands were run.

## Interface requests

None. Consume final template/abstracts; retain the FILL method and device-only
extraction scope when presenting results. Generation IDs support snapshot checks.

## Publish journal

Publish 2026-10-18T07:47:24.187502+00:00: Phase 3 compact cells, 132 um common height; phase-1 checks and fresh full characterization passed. Whole-library directory exchange; height 132 um. GDS/SPICE/extraction/abstracts/truth/PNG/characterization/verification and template belong to this generation.

Evidence publish 2026-10-18T08:07:34.359407+00:00: five-cell original/compact equivalence and four cascade protocols PASS; cell-view generation remains 2026-10-18T07:47:24.187502+00:00. Failed unseeded diagnostics retained.

Final verification 2026-10-18T08:22:49.239261+00:00: 16 CELLS tests passed; published phase-1 and phase-2 reports both passed; live input hashes unchanged.
