# SIM status — Phases 2 and 3 complete

2026-10-18. No blockers. No additional packages installed. PDK and reference checkout remained read only.

## Real PNR post-layout validation

All results below use the final selected PNR layouts and current compact
132 um cell generation. Each GateNetlist was converted to a transistor-level
reference, compared with the unmodified PDK KLayout LVS deck, extracted,
augmented with GDS-derived per-net lumped wire C and simulated with ngspice.
Pre-layout and extracted runs use the same input vectors and output loads.
All input/library hashes still match the live files at final verification.

| Design | Input vectors | LVS / pre / post | Max post error (mV) | Max estimated rail deviation (mV) | Max additional divider-zero shift (mV) |
|---|---:|---|---:|---:|---:|
| adder4 | 20 | Match / PASS / PASS | 43.340 | 13.542 | 1.822 |
| full_add | 27 | Match / PASS / PASS | 43.340 | 7.270 | 1.369 |
| mac1 | 81 | Match / PASS / PASS | 43.446 | 9.864 | 1.415 |
| mul1 | 9 | Match / PASS / PASS | 100.891 | 2.174 | 0.569 |

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
| full_add | sum | 100.57 | 109.84 | 9.27 |
| full_add | cout | 90.61 | 99.91 | 9.30 |
| mac1 | sum | 132.25 | 145.00 | 12.76 |
| mac1 | cout | 122.50 | 135.10 | 12.60 |
| mac1 | and_out | 13.30 | 17.24 | 4.76 |
| mac1 | or_out | 17.14 | 21.00 | 3.85 |
| mul1 | p | 15.69 | 17.08 | 1.64 |

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

**Phase 2 tests: 33 passed, no skips, in 132.33 s** with
`python3 -m pytest tests/sim tests/extract -q`. The final default post-layout
script also exited 0 for all four designs using the stored electrical caches.
`compileall` and `git diff --check` on owned paths pass.

## Interface requests

No shared-contract changes requested. Phase 2 used the explicit waves/example
and characterization grants. Phase 3 additionally uses `tritflow/viz/scaling.py`,
`results/`, `cells/out/sizing/` and `examples/adder_scaling.py`, as authorized.

## Phase 3 — complete (2026-10-18)

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

Both adopted source sizes pass: INV worst error **39.542 mV**, worst absolute
static rail current **407.166 µA**; NANY **44.600 mV**, **421.361 µA**. Fourteen
INV candidates fail the voltage criterion. One NANY candidate (baseline MOS,
RR length 20 µm) produces a nonphysical DC root outside the supply rails;
its metrics are null, diagnostic and raw data retained. This is a solver/model
failure, **not** evidence that the RR20 circuit cannot work. No point is dropped.

The bundled grids carry source/model/analysis hashes. `sweep_dimensions()` can
serve their rows even with no local per-row cache, including explicit failed
rows. Disposable `rows/` caches are ignored; the two portable grids and HTML
figures are published. JSON transfer arrays work directly with `transfer_figure`.
Measured warm reads: INV grid ~16 ms, NANY ~3 ms, cached failed-grid candidate
~6 ms; scaling/load JSON reads <1 ms on this workstation.

### Real-layout adder scaling, N=1…6

`results/adder_scaling.json` and `.html` contain the completed six-width study.
Every width uses public HDL/synthesis and `pnr.place_and_route` with real cells,
seed 7, normal PDK DRC, strict PDK LVS, extracted devices, actual-GDS wire C,
pre/post ngspice and the resistive IR solver. All six pass DRC/LVS and every
representative pre/post output check. No mocks or analytical delay substitutes.


| N | Cells | Die area (mm²) | Carry pre (ns) | Carry post (ns) | Worst representative static power (mW) | Max rail deviation (mV) | Max zero shift (mV) |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 16 | 0.555984 | 55.04 | 59.80 | 66.71 | 7.27 | 1.36 |
| 2 | 32 | 1.393524 | 104.27 | 115.56 | 133.41 | 9.53 | 1.33 |
| 3 | 48 | 2.136240 | 153.45 | 152.83 | 200.12 | 11.40 | 1.70 |
| 4 | 64 | 2.766600 | 202.59 | 201.91 | 266.82 | 13.40 | 1.79 |
| 5 | 80 | 4.030992 | 251.73 | 250.76 | 333.53 | 13.00 | 1.28 |
| 6 | 96 | 4.383720 | 300.88 | 299.67 | 400.23 | 13.96 | 1.83 |

Conditions: ±5/0 V, nominal 27 °C, 10 fF per output, 1 ns ramp, 1 µs per
segment, 2 ns maximum timestep, inclusive ±0.5 V band. Carry is the worst of
COUT and most-significant SUM over four directed full-length carry transitions:
positive/negative assertion and release, with A all ±1 and B all 0. Additional
zero/overflow/opposite/alternating cases give 11 states in sequence. N=1 also
visits all 27 states (38 sequence entries in total). This is the worst measured
carry case in this documented set, not exhaustive analog transition coverage.
Synthesis equivalence is exhaustive through N=5 (177,147 inputs); N=6 uses
100,000 reproducible random vectors, seed 0. The analog arithmetic oracle is
independent of gate mapping. Sub-2 ns pre/post differences remain unresolved;
the small negative differences do not establish a speedup.

Static power is `-sum(Vrail * I(source))` from independent post-layout DC solves,
not transient tails: all 27 unique states for N=1, nine documented unique states
for other widths. The maximum is scoped to those states. Large-circuit OP
convergence uses ideal internal-net `.nodeset` guesses mapped through the PDK
LVS cross-reference. These are released Newton starting guesses, never voltage
constraints or `uic`. Actual analog outputs are checked against radix arithmetic.
The IR per-rail worst-current envelope is separate from ideal-rail SPICE; metal R
and wire C retain the assumptions above. PNR heuristic choices affect area.

Artifacts: `build/adder_scaling/adderN/` contains synthesis/PNR, physical-stage
cache and `scaling.json`; `postlayout/` contains GDS/reference snapshots, strict
LVS, geometry/C, pre/post waveforms and measurements, independent vectors,
static operating points and IR. The published matrix retains all hashes,
per-transition measurements, reference vectors and evidence paths.

Producer caches validate source/model/code/options and output hashes. Python
source provenance is frozen when the producer imports its modules, matching
Python's loaded-code semantics while other streams edit files; use a fresh
producer process to pick up their edits. Live HDL, library, models, decks and
physical artifacts remain checked. Changed live cell views invalidate results.
`load_scaling()` is a fast read of the portable measured dataset; it does not
silently launch PNR. `scaling_figure()` returns four Plotly panels for area/cells,
pre/post carry, static power, and estimated rail/zero shifts.

### Full-adder post-layout output-load boundary

`results/full_add_load_sweep.json` and `.html` contain 13 measured loads. Equal
external capacitors load SUM and COUT to ground, in addition to GDS wire C.
All 27 input states are visited lexicographically (26 transitions, not all 702).
Window 500 ns, checkpoint at 499 ns, 1 ns ramp, maximum timestep 2 ns.

- Coarse loads 0.01, 0.1, 1, 3 and 10 pF pass; 30 pF is the first coarse FAIL.
- Local refinement: **12.8125 pF PASS**, **12.96875 pF FAIL** per output;
  bracket width **0.15625 pF**, below the 2% stopping criterion.
- Last PASS: worst SUM settling **498.03 ns**, COUT **422.86 ns**, maximum
  checkpoint error **0.49690 V**.
- First FAIL: SUM at `[a,b,cin]=[-1,0,-1]` checks at **4.48626 V** against +5 V,
  error **−0.51374 V**, and does not settle in its window. Its settling is null.

The bracket is local to measured points and this input sequence; no unmeasured
monotonic-load, PVT or silicon guarantee. Per-output maximum fields retain the
maximum among settled transitions; consult `unsettled`/`failures` as well.
`load_sweep_figure()` omits a pin's settling trace where it has any unsettled
transition, marks FAIL at the window, and plots check error on a second axis.
`load_sweep_results()` reads the precomputed dataset instantly;
`sweep_output_load()` validates and reuses measured evidence. Raw files live
in `build/full_add/load_sweep/`.

### Phase 3 reproduction and validation

```sh
python3 -m tritflow.sim.sizing
python3 examples/adder_scaling.py --jobs 2
python3 examples/adder_scaling.py --load-only
python3 examples/postlayout_all.py
python3 -m pytest tests/sim tests/extract -q
```

The four original PNR designs were re-extracted/rechecked against their latest
published GDS/PNR files; all pass, with every recorded input hash matching live
files. The top two tables were refreshed from those current summaries.
All six scaling evidence sets and load-sweep artifacts match their recorded
SHA256 values. No extra packages installed. No changes made outside SIM-owned
paths and the explicit sizing/results/example/viz grants.

**Final regression: 54 passed, no skips, in 145.99 s** with
`python3 -m pytest tests/sim tests/extract -q`. `compileall` and
`git diff --check` on owned paths pass. The full scaling/load producer and
the four-design post-layout producer both exited 0.
