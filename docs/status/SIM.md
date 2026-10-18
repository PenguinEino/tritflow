# SIM status — Phase 2 complete

2026-10-18. No blockers. No additional packages installed. No git-state
changes made by SIM. PDK and reference checkout remained read only.

## Real PNR post-layout validation

All results below use the final selected PNR layouts and current compact
132 um cell generation. Each GateNetlist was converted to a transistor-level
reference, compared with the unmodified PDK KLayout LVS deck, extracted,
augmented with GDS-derived per-net lumped wire C and simulated with ngspice.
Pre-layout and extracted runs use the same input vectors and output loads.
All input/library hashes still match the live files at final verification.

| Design | Input vectors | LVS / pre / post | Max post error (mV) | Max estimated rail deviation (mV) | Max additional divider-zero shift (mV) |
|---|---:|---|---:|---:|---:|
| adder4 | 20 | Match / PASS / PASS | 43.340 | 25.572 | 1.232 |
| full_add | 27 | Match / PASS / PASS | 43.340 | 9.199 | 1.374 |
| mac1 | 81 | Match / PASS / PASS | 43.446 | 11.640 | 1.351 |
| mul1 | 9 | Match / PASS / PASS | 100.891 | 2.984 | 0.774 |

`full_add`, `mac1`, and `mul1` cover **all** 27, 81, and 9 input combinations.
Adder4 uses 20 documented vectors: positive and negative four-digit carry
setup/trigger/release, both overflows, cancellation, alternating operands, and
positive/negative single-digit probes. The carry trigger changes only cin while
all four digit sums propagate the carry. Expected outputs come from independent
balanced-radix arithmetic/min/max, not the mapped gate evaluator.

Final conditions: ideal +5/0/-5 V, 27 C, 10 fF per external output, 1 ns edges,
500 ns hold, 2 ns maximum timestep. Longer 2 us qualification windows established
that 500 ns retains margin over the observed settling times; the shorter default
keeps the notebook practical. The acceptance band remains inclusive ±0.5 V,
checked 1 ns before hold end. Settling is final band entry measured from ramp
start, with the output required to remain in band through segment end.

| Design | Output | Max pre settling (ns) | Max post settling (ns) | Largest same-transition increase (ns) |
|---|---|---:|---:|---:|
| adder4 | sum[3] | 202.55 | 201.81 | 0.00 |
| adder4 | sum[2] | 153.38 | 152.81 | 0.00 |
| adder4 | sum[1] | 123.06 | 122.15 | 0.00 |
| adder4 | sum[0] | 123.73 | 122.73 | 30.38 |
| adder4 | cout | 192.74 | 191.64 | 0.00 |
| full_add | sum | 100.57 | 109.87 | 9.30 |
| full_add | cout | 90.61 | 99.78 | 9.17 |
| mac1 | sum | 132.25 | 145.12 | 15.59 |
| mac1 | cout | 122.50 | 135.27 | 13.51 |
| mac1 | and_out | 13.30 | 16.27 | 3.39 |
| mac1 | or_out | 17.14 | 20.61 | 3.70 |
| mul1 | p | 15.69 | 16.94 | 1.92 |

The two maxima can occur on different transitions. The last column compares
the same transition; it is not the difference of independently selected maxima.
Every per-transition value, including negative changes, is in summary.json.
Wire C can filter hazards as well as slow edges. Crossing interpolation is
limited by the maximum timestep; sub-2 ns differences are unresolved and do
not establish a speedup. These are nominal simulation estimates.

Each `build/<design>/postlayout/` contains:

- `inputs/`: exact GDS, GateNetlist JSON and PNR JSON consumed by the run.
- `library/`: consumed cell GDS, schematic/extracted SPICE, abstracts,
  characterization, and template snapshots.
- `lvs/`, `lvs.json`: strict comparison database, raw extraction, reference and log.
- `capacitance.json`, `postlayout.spice`: actual connected-net metal areas,
  perimeters and added lumped capacitors.
- `vectors.json`: declared input order, labels and independent expected outputs.
- `pre/`, `post/`: decks, logs, ASCII waveforms, compressed numpy waveforms,
  measurements and electrical-experiment cache manifests.
- `ir_drop.json`: signed current, per-cell rail voltages and midpoint shifts.
- `waveforms.html`: standalone Plotly pre/post overlay with ideal levels,
  acceptance bands, checkpoints, PASS/FAIL marks and settling annotations.
- `summary.json`: hashes, conditions, aggregate checks and transition differences.

The runner detects cell revision changes by comparing embedded GDS masters with
current library polygons, then checks every source hash again at completion.
Several intermediate PNR seed revisions changed during simulation: those runs
were rejected as stale and rerun. The final fresh pass and a subsequent cached
invocation of `python3 examples/postlayout_all.py` both exited 0 for all designs.
No stale result is presented as current. Identical electrical experiments can
reuse measured waveforms; model contents, circuit, vectors, expected values,
loads and timing all participate in the cache key. Measurements are recomputed
from cached arrays. Per-design and per-waveform locks serialize writers.

## Measured cascade and fanout

`build/cascade/current/` and each `cells/out/<CELL>/<CELL>.char.json` now include
self-loading measurements. The source hash matches each compact extracted cell.

| Cell | Suggested max fanout | Worst five-stage chain settling (ns) | Worst driver settling with 8 receivers (ns) | Max cascade/fanout level error (mV) |
|---|---:|---:|---:|---:|
| INV | 8 | 15.11 | 36.03 | 39.537 |
| NAND | 8 | 35.50 | 65.33 | 104.283 |
| NOR | 8 | 64.53 | 94.50 | 158.938 |
| NANY | 8 | 70.26 | 144.89 | 106.491 |
| BUF | 8 | 27.05 | 37.87 | 35.656 |

Counts 1/2/4/8 were measured using actual receiver transistors. For two-input
cells, each receiver pin is tested separately with the other pin held at each
of -1/0/+1. Every receiver output has 10 fF. Five-cell chains use a neutral
second input (NAND +1, NOR -1, NANY 0), with 10 fF only at the final stage.
Every driver input state and all six directed scalar level transitions are
covered. Isolated-cell characterization separately covers every directed input
vector transition at 10 fF / 100 fF / 1 pF.

All driver and receiver outputs and all five chain stages pass the voltage
band. Fanout 8 is the **largest tested count**, not a claim about higher fanout
or PVT. Recommendations now rest on measured loading/restoration; previous
capacitance-only estimates remain as `fanout.capacitance_estimate_max`.
The synthesis default fanout 4 remains within the measured nominal bound.

The saved reference in `~/balanced-ternary-logic/simulation/cascade` is an older
**RR20** two-inverter test. Its circuit was replayed read-only with the saved
input sequence, 20 ns holds and 1 ns edges. Output checkpoint disagreement is
7.75e-8 V maximum. Current library measurements use **RR30**, so their timing is
reported separately. Reference results are in `reference.json`. Five-stage
Plotly figures are `<CELL>.chain.html`; INV/NANY DC/current figures are
`<CELL>.transfer.html`.

## Harness and extraction decisions

- Parse actual subcircuit formal order; extracted designs need not use the
  contracted cell order. GateNetlist references enforce that cell contract.
  Bit-blasted names such as a[0] are quoted in Nutmeg expressions.
- ngspice runs isolated, without user startup files, with deterministic stimuli,
  absolute PDK includes, timeouts and finite-data/completion checks. Default
  1e12 ohm shunts and .nodeset guesses aid OP convergence; no uic constraints.
- Accept only a few ulps of decimal final-time roundoff, never real truncation.
- PDK comparison statuses, errors and success text are checked, plus explicit
  case-insensitive top signal/power formal equality. The deck alone accepts
  some missing top ports; an injected missing output is still rejected.
- The PDK purges unloaded physical rails. A missing power formal is restored
  only after recursively proving it reaches no device terminal in the reference.
  Raw extraction is retained. Signal formals are never repaired this way.
- Persisted LVS metal can omit purged floating rails. Match exact geometry
  first, otherwise the unique largest registered subset of the physical metal;
  report excluded area explicitly. Add C only to retained connected nets.
- Extraction-only mode without reference returns matched=null, report=null.

## Model limits

Wire C is an **assumption**, not calibrated PEX: epsilon_r=3.9, effective M1/M2
heights 1/2 um, area terms 0.03453/0.01727 fF/um² and fringe 0.02 fF/um perimeter.
No interconnect coefficients were found in the installed PDK; OS00 lists
parasitic extraction unavailable. Metal polygons are merged before measurement.
GDS C includes connected cell-pin metal; child-only local nets, coupling,
shielding, via C, poly parasitics and signal-wire R are outside this estimate.
The PNR geometry alternative measures routed wires/pins only; do not add both.

IR uses assumed 0.05 ohm/square on both metals, 0.05 ohm per via, Manhattan
centerlines, fixed supply pads and constant nominal-bias characterized currents.
The metal estimate corresponds roughly to assumed aluminum rho=2.5e-8 ohm*m /
0.5 um thickness. Per-rail worst-magnitude currents are an envelope, not one
common logic vector. No package, thermal, current-spreading or local-voltage
iteration is included. Floating supply islands are errors. INV/NAND/NOR zero
shift is an additional equal-divider estimate; NANY reports its local VMID.
SPICE runs retain ideal supplies; the IR estimate is reported separately.

Transient tail rail currents are estimates. Static currents use independent
DC operating points, with SPICE sign positive into the ideal rail source.
Input C is -Im(I(Vin))/(2*pi*1 MHz), one input at 1 V AC, other inputs/rails
AC grounded and output unloaded, at every trit bias, including Miller response.
No PVT or silicon qualification is claimed.

## JSON and notebook API

Cell characterization schema version remains 1 with backward-compatible fields:
`source_sha256`, `model_sha256`, `conditions`, per-vector `dc`,
`max_static_current_a`, `input_capacitance`, and load-dependent `transient`.
Each output records ideal_trit, voltage_v, signed error_v, passed, settling_s;
unsettled times are null. A null maximum with no transitions has unsettled=0.
Ties have no input-transition or cascade recommendation.

Phase 2 adds `cascade` (source hash, vectors, conditions, tested counts, five-stage
results and all per-case measurements) and replaces `fanout` with suggested_max,
tested_counts, chain_depth, method, scope and capacitance_estimate_max. A
recommendation requires five-stage restoration and all loading cases through
the recommended count. JSON never contains NaN/Infinity.

`tritflow.viz.waves.waveform_figure(result, pre=...)` returns a Plotly Figure
with three ideal levels, ±0.5 V bands, ideal steps, check markers, worst or all
settling arrows and optional pre/post overlay. `transfer_figure(result, input,
outputs)` places signed static source current on a second axis. Both return
figures without opening browsers or changing global renderers. Tests live in
SIM-owned paths. More API examples are in `tritflow/sim/README.md` and
`tritflow/extract/README.md`.

## Reproduction and tests

```
python3 -m tritflow.sim.cascade --out build/cascade/current
python3 examples/postlayout_all.py
python3 examples/postlayout_all.py --watch --watch-seconds 600
python3 examples/postlayout_all.py --rebuild-pnr
python3 -m pytest tests/sim tests/extract -q
```

The post-layout script consumes PNR outputs; --rebuild-pnr invokes the public
PNR API with its normal DRC checks. Snapshot/hash validation follows compact-cell
changes. The cascade command reuses matching source-hash reports and refuses
mixed revisions. Requirements are the existing numpy/scipy/Plotly/klayout,
ngspice, KLayout binary and TR-1um PDK. Optional reference regressions require
`~/balanced-ternary-logic` and copy its GDS/netlists into temporary directories.

**Final tests: 33 passed, no skips, in 132.33 s** with
`python3 -m pytest tests/sim tests/extract -q`. The final default post-layout
script also exited 0 for all four designs using the stored electrical caches.
`compileall` and `git diff --check` on owned paths pass.

## Interface requests

None. Newly granted ownership was used only for `tritflow/viz/waves.py`,
`examples/postlayout_all.py` and generated result paths, alongside prior SIM
paths and the explicitly authorized cell characterization JSON files.

## Phase 3 — in progress (2026-10-18)

`tritflow.sim.sizing.sweep_dimensions` implements FRONTEND's exact proposed
signature/schema. Canonical device IDs and adopted W/L come from the published
schematic, candidates inherit unspecified dimensions, every trit state has its
own DC operating point, and errors remain explicit failed rows. Successful rows
are content-addressed by source/models/analysis code/conditions. Supplying
`workdir` retains independent transfer/DC decks and logs. Published cells and
PDK files are never edited by the experiment.

Precomputed `cells/out/sizing/INV.grid.json`: **90 candidates, 76 PASS**;
`NANY.grid.json`: **18 candidates, 17 PASS**. INV varies MP/MN W, common MOS L,
and both RR lengths; NANY varies common MOS W factor/L and both RR lengths.
`load_grid()` reads slider data immediately; `sweep_dimensions()` also reuses
individual candidate caches. `python3 -m tritflow.sim.sizing` reproduces both.
`tritflow.viz.scaling.sizing_figure()` marks `adopted_index` with a star.

Actual-layout adder scaling and the 500 ns full-adder load boundary are running.
They use the existing strict PDK LVS/real-GDS wire-C/IR pipeline, independent
radix-3 carry oracles and source/artifact fingerprints. Completed measurements
and the final reproduction/test commands will be recorded below.
