# CELLS — compact Phase 3 complete; Phase 2 in progress

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

## Phase 2 — running

Fresh Xschem references and fresh PDK extraction of the actual taped-out GDS
are being compared with the compact generation. Original and compact INV,
NAND, NOR and NANY all strictly match those independent source schematics.
INV/NAND/NOR DC grids and every directed transition at 10/100 fF have completed
with zero original/compact differences. NANY skew and cascade suites are running.
The added six-NANY tied-input cascade initially reached the same nonphysical
BSIM root in both original and compact networks; its failed report is retained
as `equivalence_report.unseeded.json`. Connectivity-based initialization is
being refined; no cell geometry/device changes are implicated.
BUF is additionally checked against two copies of the fresh independent INV
source/extraction. New support cells have no taped-out counterparts.

Planned report: `cells/out/equivalence_report.json`. Retained runnable decks,
logs, unmodified source extraction and compressed DC/cascade data live under
`cells/out/equivalence/`. Protocols include 0.125 V DC grids, +/-0.5 V input
neighborhoods, separate true static-current operating points, all 6/72 directed
transitions with 100 ns holds / 1 ns edges / 0.1 ns max step, NANY 2 ns A/B skew,
and original two-INV, six-NOR (A/B/tied), mixed-six and added six-NANY cascades.
Historical TB embedded RR20 values are superseded by fresh RR30 circuits;
their stimulus/check protocols are retained.

These comparisons include extracted intrinsic junction/device parasitics, **not
interconnect RC**, PVT/mismatch, package/pad effects or manufacturing signoff.
Identical intrinsic parameters imply any small differences are numerical; no
routing-dependent delay claim should be inferred from device-only extraction.

## Commands / dependencies

`python3 -m tritflow.cells build` privately builds, qualifies, characterizes and
publishes a complete generation. `verify` runs phase-1 checks; `equivalence`
runs phase 2 against `~/balanced-ternary-logic`. `--out` selects a private stage.
`python3 -m pytest tests/cells -q` now includes the ported Phase 2 checks and is
running against an independently rebuilt private compact library.

No extra packages installed. No reference or PDK files changed. Only owned paths
were edited. No git-state-changing commands were run.

## Interface requests

None. Consume final template/abstracts; retain the FILL method and device-only
extraction scope when presenting results. Generation IDs support snapshot checks.

## Publish journal

Publish 2026-10-18T07:47:24.187502+00:00: Phase 3 compact cells, 132 um common height; phase-1 checks and fresh full characterization passed. Whole-library directory exchange; height 132 um. GDS/SPICE/extraction/abstracts/truth/PNG/characterization/verification and template belong to this generation.
