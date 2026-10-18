# Ternary static timing

`analyze(netlist, pnr=None)` uses measured midpoint propagation, measured output
slew and one endpoint settling term. No SPICE runs during analysis, plotting or
validation. Independent characterization is an offline producer.

Without vector pairs, the default uses transition-specific slew windows and
symbolic primary-input compatibility. With complete `vector_pairs`, it uses the
unchanged matched-event model. The two claims are separate:

- Default bound: all **838 saved observations / 799 transition observations**
  covered, **zero underpredictions**, **1.026–3.072×** measured output maxima,
  mean **2.182×**. The requested 1.5× target is **not achieved** (2/39 outputs).
- Matched accuracy: **38/39 within ±20%, MAPE 6.782%**, unchanged from phase 2.
  Scaling adder2 `cout` remains the documented partial-pulse outlier.

```python
from tritflow.sta import analyze
from tritflow.sta.plot import validation_figure, pessimism_figure

report = analyze('build/full_add/full_add.json',
                 'build/full_add/full_add.pnr.json')
print(report.arrival)  # output -> seconds
for stage in report.critical_path:
    print(stage.instance, stage.input_transition, stage.output_transition,
          stage.delay_s, stage.settling_tail_s)
report.to_html('results/sta/full_add.html')
validation_figure().show()  # matched accuracy, optional separate bound trace
pessimism_figure().show()   # bound / measured maximum
```

GateNetlist objects/dicts and PnrResult objects are accepted. Loads sum each
connected pin's maximum measured biased AC input C, supplied wire C, and output
test C (10 fF by default). `output_load_f` accepts a scalar or output-name dict.
`wire_caps={logical_net: farads}` overrides the PNR route estimate. Validation
uses SIM's exact LVS-mapped top-net GDS C, including cell terminal metal once.
All loads are identical to phases 2/3; no fitted C or delay multiplier is used.

## Measurements and composition

For the actual old/new ideal levels:

```
p50 = t50(output) - t50(input)
slew = t90(output) - t10(output)
tail = final entry into the ideal ±0.5 V band - t50(output)
next_t50 = input_t50 + p50
next_equivalent_full_ramp = slew / 0.8
endpoint_settling = endpoint_t50 + endpoint_tail
```

Only midpoint propagation composes. Intermediate band-entry tails overlap the
next gate's response and are not added. The midpoint for −1→0 is −2.5 V; for
−1→+1 it is 0 V. Last directional crossings and their counts are retained.
Negative p50 is allowed. Stable-output classes have scalar recovery, no
invented midpoint or full-level slew.

STA-owned tables at `results/sta/propagation/tables/` contain **175 profiles /
7,980 observations** from five extracted cells, all passing. Loads are
10/100/500/1000/2000 fF; full ramps are 0.25/1/5/15/50/150/**200 ns**. Phase 4
added 25 independent SPICE profiles at 200 ns. All previous measured rows are
unchanged. Extraction/model hashes and CELLS generation must match the current
publication. Real decks, logs, measurements and representative waves are kept.
No circuit-level simulation is used to fit these tables.

Interpolation is bilinear in physical units. Failed/null points are rejected.
The explicit `linear` load policy permits extension down to zero or up to twice
the largest measured load; `load_policy='error'` forbids it. No present load
needs extension. The default bound **raises on out-of-domain slew**, rather than
clip it. The current 39-output label domains close within 200 ns.

## Tightened global analysis

A label carries a local output transition and a narrow equivalent-ramp interval
(default 5 ns bins). The measured output-slew function transports each interval
to the next gate. Splitting at input knots and output-bin crossings retains
piecewise-linear extrema. The endpoint contribution maximizes d50 + tail on
the same segment; it does not splice independent worst tails onto a path.

Backward search intersects primary-input conditions along the whole path.
Transient side-input states include both settled endpoints and intermediate
logical values. Their time alignment and pulse amplitude are still relaxed.
The report supplies `compatible_primary_endpoints` for these constraints;
`before`/`after` are null because this is **not** a jointly realizable temporal
waveform witness. Stable recovery remains a local measured endpoint term; it
is not promoted to an arbitrary full-level transition at every next gate.
Propagation of partial analog recovery is explicitly unmodeled.

The old broad relaxation increased timing mainly through arbitrary slow ramps:
95.34% of its increase over the fixed-ramp/no-guard/no-tail baseline came from
ramp relaxation, 2.58% from recovery activity and 2.08% from the endpoint tail
(order-independent three-factor attribution). Narrow measured slew windows
reduce mean bound/max from 6.016× to 2.182×, without changing matched accuracy.

The 1.5× target is not justified by the current scalar tables. Removing
transient classes misses three saved observations. Smaller bins converge above
the target: adder2 `cout` changes from 186.86 ns at 1 ns bins to 185.85 ns at
0.25 ns bins. An exact-circuit replay of that model-selected endpoint vector
settles in 152.35 ns, versus the original sequence's 105.36 ns maximum. Only
5.68 ns remains below a 1.5× ceiling, while the same-pattern event and window
models are respectively 20.13 ns and 33.50 ns high. Unequal input ramps/skew,
partial pulses and waveform shape require additional characterization and
joint timing history to justify tighter global constraints. This does not
prove a 1.5× physical bound impossible; it records why it is not achieved here.

`worst_case_conservative` describes coverage of the saved nominal dataset.
`certified_analog_bound` remains false. The smallest measured margin is only
0.408 ns; source sampling and unmodeled waveform effects preclude treating
this as signoff margin. PVT, calibrated signal/poly RC, coupling and package
are also outside the model.

## Modes, artifacts and reproduction

- Default `global_mode='windows'`: compatible transient slew windows.
- `global_mode='endpoint'`: diagnostic fixed-ramp, exact settled endpoint graph.
- `global_mode='envelope'`: broad independent ramp/recovery relaxation over the
  current table domain. Archived phase-3 tables retain the original 150 ns axis.
- Explicit legacy `TimingLibrary`: historical additive settling ablation.
- `vector_pairs=[(before, after), ...]`: matched ordered events; flags
  `ordered_events=False` / `propagate_slew=False` select the block/fixed-ramp
  accuracy ablations. All pairs must specify every primary input.

Current publication: `results/sta/validation.json` (schema 4), twenty timing
reports, `validation.html`, `pessimism.html`. Phase-4 attribution, candidate
comparisons, source audit and independent SPICE witnesses are under
`results/sta/phase4/`. `tightening.html` compares all 39 old/new factors against
1.5×. Phases 1–3 are preserved in their own archive directories.

```sh
python3 -m tritflow.sta.validate
PYTHONPATH=. python3 results/sta/phase4/audit.py
python3 -m pytest tests/sta -q

# Optional diagnostic reproduction; isolated cell/circuit SPICE only in STA paths:
PYTHONPATH=. python3 results/sta/phase4/attribute.py
PYTHONPATH=. python3 results/sta/phase4/windows.py
PYTHONPATH=. python3 results/sta/phase4/exact_witness.py
python3 -m tritflow.sta.characterize --jobs 2
```

Validation fingerprints foreign results, consumed physical evidence, current
cell tables, STA surfaces and executing source before/after calculation.
Changed publications trigger retries; `--watch-seconds` repeats on later
changes. No foreign producer is started or stopped.
