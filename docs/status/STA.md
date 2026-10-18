# STA stream — complete

2026-10-18. Qualified against public PDK
`5d963db9d44e192d37a0489c208bfccf2e2f690c`, with CELLS generation
`2026-10-18T10:26:47.211617+00:00`. Read AGENTS.md, concept, interfaces, STA
brief and CELLS/SIM/PNR status before implementation. Only STA-owned paths were
changed. No packages installed, reference/PDK edits or git state changes.

## Done

- Published-table load/ramp interpolation with source/generation checks,
  explicit extrapolation policy and failed/null-sample rejection.
- Graph STA with separate directed ternary transitions, exact settled endpoint
  sensitization through reconvergent logic, and complete critical-path patterns.
- `tritflow.sta.analyze(netlist, pnr=None) -> TimingReport` exposes `.arrival`,
  `.transition_arrival`, `.critical_path`, `.sensitizing_pattern`, `.to_html()`
  and JSON serialization. Each path stage lists cell/instance/pin/net, both
  transitions, complete from/to pin values, arc ID, C and timing contribution.
- Fanout input C + public extraction route C + external output load; explicit
  logical-net capacitance override for full-GDS validation.
- All six scaling adders and all four examples validated, **39 output rows**.
  `results/sta/validation.json` reports `complete:true`,
  `qualified_current:true`, `stable_snapshot:true`. These flags describe
  coverage, source freshness and pinned provenance, not timing accuracy.
- Plotly notebook figures `timing_figure(report)` and `validation_figure()`;
  portable comparison at `results/sta/validation.html`.
- Tests: **8 passed in 9.58 s**. Includes independent exhaustive small-circuit
  timing comparisons, reconvergence/false paths, tied inputs, constants,
  restricted vectors, bilinear interpolation/domain failures, source integrity,
  load accounting, HTML, content-fingerprint changes and a real six-trit adder
  with its critical-path pattern checked through every cell.

## Decisions / electrical limits

- Consume CELLS schema-1 `.timing.json`, including synchronous multi-pin
  observations and per-pin maximum biased AC input C. A partial `.char.json`
  sequence cannot replace missing directed timing surfaces; fail explicitly.
- Linear interpolation in physical load/ramp units. Current measured axes are
  5 fF–1 pF and 1–150 ns full linear ramps. Cell sampling defaults to strict;
  graph analysis defaults to **explicit, recorded** endpoint load extension
  between zero and twice the largest measured load, using the closest two
  columns and flooring negative estimates at zero. `load_policy="error"`
  disables this. Never extend ramps or interpolate failed/null samples.
  Some real adder nets exceed 1 pF, so extensions remain uncharacterized.
- Keep every graph predecessor per transition. Best-first backward search uses
  graph arrival envelopes as search bounds and reduced ternary decision diagrams
  to intersect all endpoint conditions. Alternate paths remain available at
  reconvergence. The first satisfiable leaf is the largest additive-model path.
  Resource limits raise, without sampling, beam truncation or partial success.
  Search-only symbolic nodes are released between output-transition queries.
- Add measured cell settling using a **fixed full 1 ns ramp at every stage**.
  The ramp axis is available through `input_transition_s`, but waveform slew is
  not propagated. There is no waveform-shape/skew model; intermediate glitches
  with unchanged settled endpoints cannot propagate through the graph. Local
  unchanged-output recovery is retained at the output where characterized.
  Synchronous multi-pin observations cannot validate arbitrary input skew.
- The endpoint pattern proves settled logical consistency at every stage, not
  analog realization of the listed delay. **No guaranteed upper-bound claim.**
  Ties have no signal transition delay; power-up/rail settling is outside scope.
- Fanout uses maximum biased device input C. The public default PNR estimator
  merges routes/external pins, excluding cell terminal metal. Validation instead
  uses SIM's same LVS-mapped full top-net GDS C, including connected terminal
  metal exactly once. Default external output load is 10 fF. Intrinsic devices
  and timing tables remain device-only. Metal C coefficients are assumptions;
  calibrated poly/signal RC, coupling, PVT and package effects are absent.
- Compare all-endpoint STA and STA restricted to SIM's actual consecutive
  input pairs separately. SIM's finite-vector maxima are not global analog
  bounds, and the restricted estimate still does not reconstruct analog history.

## Validation evidence and honest error ranges

All numerical results are from current pinned-PDK physical snapshots. Initial
validation encountered SIM's actively running N=6 refresh and recorded it as
incomplete. The refresh completed; validation reran for the new publication and
subsequent `results/` changes, without starting/stopping foreign producers.

The present additive/max-biased-C model is **strongly pessimistic** and should
be presented as a coarse analytical estimate, not a precise SPICE substitute.
On the **same tested endpoint pairs**, signed errors across 39 output maxima
are **+47.60% to +98.49%**, mean absolute percentage error **70.31%**, MAE
**121.73 ns**, maximum absolute error **281.35 ns**. For all endpoint pairs,
the corresponding observed range is **+70.98% to +268.45%**, MAPE **164.53%**,
MAE **296.51 ns**, maximum absolute error **687.70 ns**. No underprediction was
observed in this finite nominal dataset; that is not a proof of a bound.
`accuracy_passed` is null because the brief specifies no accuracy threshold.
No empirical scale factor is fitted to make the comparison appear closer.

The table gives worst over outputs (ns); full per-output values, errors,
transition arrivals and input patterns are retained in the JSONs. "All" has
broader endpoint coverage than the simulated sequence; "Tested" uses that
sequence's exact consecutive endpoint pairs.

| Design | SPICE | STA all | STA tested | Extended-load instances |
|---|---:|---:|---:|---:|
| scaling/adder1 | 139.90 | 241.49 | 216.29 | 2 |
| scaling/adder2 | 142.54 | 388.18 | 222.09 | 4 |
| scaling/adder3 | 169.46 | 540.40 | 292.26 | 6 |
| scaling/adder4 | 231.81 | 705.71 | 407.17 | 11 |
| scaling/adder5 | 286.55 | 864.14 | 516.87 | 16 |
| scaling/adder6 | 343.68 | 1019.61 | 623.18 | 18 |
| example/adder4 | 231.80 | 705.71 | 407.17 | 11 |
| example/full_add | 108.63 | 239.03 | 200.30 | 2 |
| example/mac1 | 147.56 | 313.77 | 241.26 | 2 |
| example/mul1 | 17.14 | 44.54 | 27.27 | 0 |

The recorded all-endpoint N=6 run took 9.27 s under concurrent stream load;
its tested-pattern analysis took 0.079 s. Runtime is host/load dependent.

Validation fingerprints **all foreign `results/` content**, consumed physical
JSON/LVS evidence, cell timing/source files and generation before/after reading.
Changed content triggers a retry; optional watch mode repeats on later changes.
SIM's historical `inputs_unchanged` flag is independently checked against live
source hashes. Every design records actual model/deck pin qualification and
stale paths. Imported STA code hashes are frozen and code changes require a
fresh producer, preventing new-file hashes from describing old loaded code.

## API / reproduction

```python
from tritflow.sta import analyze
from tritflow.sta.plot import validation_figure

r = analyze("build/full_add/full_add.json", "build/full_add/full_add.pnr.json")
print(r.arrival, r.sensitizing_pattern)
for stage in r.critical_path:
    print(stage.instance, stage.cell, stage.input_transition,
          stage.output_transition, stage.delay_s)
r.to_html("results/sta/full_add.html")
validation_figure().show()
```

```sh
python3 -m pytest tests/sta -q
python3 -m tritflow.sta.validate
python3 -m tritflow.sta.validate --watch-seconds 600
python3 -m compileall -q tritflow/sta tests/sta
```

More API/model details are in `tritflow/sta/README.md`. No SPICE is launched
by these analysis/plotting/validation commands. Validation writes only under
`results/sta/`. Final compile and owned-path whitespace checks pass.

## In progress / blockers / interface requests

None. Later SIM publications can refresh the complete comparison with the
same producer/watch command. No shared interface changes are requested.
