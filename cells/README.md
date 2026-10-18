# TritFlow compact cell library

```sh
python3 -m tritflow.cells build
python3 -m tritflow.cells verify
python3 -m tritflow.cells equivalence
python3 -m tritflow.cells parasitic
python3 -m tritflow.cells timing --jobs 3
python3 -m pytest tests/cells -q
```

The live library uses a 132 um row height and 6 um routing grid. It adapts the
taped-out device placements and local wiring. M2/V1 is used for compact internal
crossovers and rail extensions. Abstracts include exact rectangular decompositions
of M1, M2 and V1, plus full-height free M2 track coordinates/counts, calculated
for a 3.4 um M2 wire and 2 um spacing. Public terminals remain accessible M1 pads.

`TR1UM_PDK` selects the PDK (default `~/pdk/TR-1um-pinned`); `KLAYOUT_BIN` selects the
binary (default `~/bin/klayout/klayout`). Build/verify accept `--out DIR` for
private staging and `--cells INV NANY` for focused work. A live build always
builds all nine cells privately, runs official DRC/LVS/DC, regenerates full SIM
characterization and timing tables, then atomically exchanges the whole output directory. A focused
build must use a private output directory. Existing consumers should read
`generation.json` before/after a multi-file load if they need a snapshot check.

`cells/template.json` points to `out/template.json`, so template and cell views
switch as one generation. `out/library.json` lists relative paths. Each electrical
cell has PCell GDS, schematic and extracted SPICE, abstract, truth table, PCell
parameters, a KLayout PNG, characterization, DC sanity results and check logs.
`all.spice` contains schematic subcircuits; include the PDK model index separately.
The original 462 um generation is preserved by the integrator's `cells-v1-tall` tag.

The drawing DRC is run without disabled warnings or waiver regions. The abutment
fixture checks all ordered cell pairs in every R0/MY combination (324 cases).
Top-level labels identify each fixture's exposed inputs, as allowed by the PDK's
external-terminal text rule. Regression tests drop real PDK V1/M2 pads at every
advertised access, in both orientations, and DRC-check the resulting fixture.

All RR use W/L=2.8/30 um; MOS dimensions and body nets match current source
schematics. BUF contains two INV circuits. Each tie has one RR30 between its
selected rail and Y, with the well/guard at VDD; it has finite drive. FILL contains
rails, nwell continuity, and body contacts. The upper nwell band spans each cell
at y=116–132 um. VDD/VMID/VSS rails are y=124–132, 6–10 and 0–4 um. The original
local VSS stripe at y=12–15.4 is retained and connected to VSS through an M2 bridge.

The PDK purges unused rail formals. Public `.ext.spice` restores only their unused
formal pins and reorders ports to signals then VDD VMID VSS. Device topology and
intrinsic junction parameters are retained; `extracted.raw.spice` is unmodified.
Device-free FILL is also purged. Its standalone mismatch is retained, and its
qualification requires empty extraction, geometric rail/well coverage and strict
LVS of a three-rail resistor-probe fixture. No phantom filler device is added.

Phase 2 writes `out/equivalence_report.json`. It freshly netlists the independent
source schematics and strictly compares both original GDS and compact GDS. It
then compares the original/compact device networks using 0.125 V DC grids with
+/-0.5 V input neighborhoods, true DC rail currents, every directed transition
at 10/100 fF, NANY A/B input-skew cases, and inverter/NOR/NANY/mixed cascades.
Runnable decks, logs, raw reference extraction and compressed DC/cascade samples
are retained under `out/equivalence/`. Historical TBs with stale RR20 values are
not used as circuit definitions; their stimulus protocols are ported onto RR30.

The Phase 2 table proves device-level identity only: neither extraction contains
interconnect parasitics, so identical results do not establish layout performance
equivalence. `parasitic` separately annotates both original and compact extracts
using SIM's public actual-GDS M1/M2 wire-C estimate, then repeats the same electrical
protocols. It adds `parasitic_aware` to the report, including per-net capacitance,
retained annotated decks and a geometric poly-resistance assessment. Both layouts
must pass the original functional limits; timing differences need not vanish.
The default command stages a complete snapshot and publishes atomically; use
`--out DIR` to compare privately after `equivalence` has run there.

Wire C uses explicit engineering coefficients, not a calibrated PDK PEX deck.
Poly R/C, wire resistance, coupling, shielding, via C, process corners, mismatch,
pads/packages and manufacturing qualification remain outside the Phase 4 simulation.
Source-level W/L experiments belong to SIM's
`tritflow.sim.sizing.sweep_dimensions`, not physical cell generation.

Phase 6 adds `<CELL>.timing.json` for STA. Five logic cells have every directed
input-vector transition at eight loads (5 fF to 1 pF) and four full linear input
ramps (1/10/50/150 ns). Single-pin arcs retain the exact side-input trits;
simultaneous multi-pin changes are separate. Matrix order is `[ramp][load]`.
Delay is final entry into the new ideal output's ±0.5 V band, measured from input
edge start and staying through the observation end. The primary model is the
device-only extraction; fanout pin C comes from biased 1 MHz AC measurements,
and STA adds actual-GDS wire C separately. Null/failed entries must remain
explicit, and neither axis may be implicitly extrapolated. Ties and FILL have
no input arcs. The full schema and numerical limits are in `docs/status/CELLS.md`.

`<CELL>.poly.spice`, `.poly.json` and `.poly.timing.json` separately model field
gate-poly sheet resistance and measure its effect at 10/100/1000 fF with
1/150 ns ramps. A reduced 0.25 um sheet mesh uses the PDK's RS resistor-poly
120 Ω/square **as an uncalibrated GC sensitivity proxy**. It does not change
the structural extraction or primary STA model. Paired baselines use the same
transient timestep. No poly C or contact resistance is invented.

The `timing` command snapshots and atomically publishes the entire library;
`--out DIR` measures a private existing library instead. It can take several
minutes. Notebook/STA consumers read the published tables without running SPICE.
Root `timing_report.json` and `poly_timing_report.json` summarize completeness,
pass flags and generation; decks, logs and per-condition measurements remain
under each cell's `timing/` and `timing_poly/` directories.
