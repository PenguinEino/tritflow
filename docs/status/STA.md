# STA stream — phase 2 complete, one documented accuracy exception

2026-10-18. Only STA-owned paths were changed. No packages installed, PDK or
reference edits, foreign producer/process changes, or git-state changes.
Qualified inputs remain public PDK `5d963db9d44e192d37a0489c208bfccf2e2f690c`
and CELLS generation `2026-10-18T10:26:47.211617+00:00`.

## Outcome

The same ten designs and **39 outputs** have been revalidated. The new measured
midpoint/event model achieves **38/39 within ±20%**, MAPE **6.78%**, MAE
**10.48 ns**, RMSE **13.36 ns**, and signed errors **−7.90% to +36.48%**.
`results/sta/validation.json` is schema 2, `complete:true`,
`qualified_current:true`, with **`accuracy_passed:false`** for the one remaining
exception. No output is dropped and no empirical delay scale factor is fitted.

The new Plotly figure is `results/sta/validation.html`, also available through
`tritflow.sta.plot.validation_figure()`. It shows matched-pattern event timing;
the fixed-ramp global graph is a separate optional legend trace. Phase-1
reports are preserved under `results/sta/phase1/`.

**25 STA tests pass.** The latest full run took 21.61 s under concurrent
verification; tests include both independent exhaustive endpoint checks and
real six-trit default midpoint timing. Characterization identities, signed
midpoint delays, endpoint-tail-only composition, slew transport, reconvergent
logical pulses, resource-limit rejection, source integrity, publication/cache
races, HTML and figure behavior are covered.

## Diagnosis before changing the timing model

Internal SPICE probes replayed the original full-adder and six-trit sequences,
with the exact original circuit, initial guesses and stimulus. Only probes and
sampling changed. Files are under `results/sta/diagnosis/`; the reproducible
audit is `phase1_audit.json` (`python3 -m tritflow.sta.diagnose --audit`).

1. **Settling times do not compose.** The phase-1 full-adder sum path adds
   192.16 ns, while the same vector's SPICE output settles in 98.05 ns. Its
   internal input-midpoint-to-band tails sum to 170.85 ns and overlap later
   gate responses. The analogous six-trit high-sum path adds 623.18 ns versus
   298.93 ns for its selected vector, with 507.41 ns of overlapping internal
   tails. Summing measured midpoint differences and only the endpoint tail
   telescopes to the observed result; that identity diagnoses the reference
   metric and is not presented as independent prediction validation.
2. **Table edge conditions differ from circuit edges.** The full-adder path's
   measured 10–90% input slews range from 0.8 to 76.8 ns, rather than a fixed
   0.8 ns. The six-trit negative-carry case spans about 1–88.35 ns as equivalent
   full linear ramps. A fixed 1 ns ramp after changing the propagation metric
   substantially underpredicts delay; output-slew propagation is necessary.
3. **Endpoint feasibility does not prove transient class excitation.** The
   original symbolic graph rejects impossible settled endpoint assignments,
   but synchronous multi-pin surfaces do not describe skewed reconvergence.
   Probed per-pin midpoint differences can even be negative when another pin
   drives the output earlier. The worst full-adder sum is an endpoint-stable
   glitch. Ordered intermediate pin states and pulse history are necessary.

The models retain the same published maximum biased AC input C throughout the
comparison. A separate finite-input-charge experiment (`results/sta/charge/`)
produced signed, strongly state-dependent multi-terminal charge, including
negative inferred capacitances. It is explicitly **not adopted** as a positive
shunt-C replacement. This does not justify a load-capacitance correction or a
circuit-delay fit.

## Measured propagation contract and implementation

STA characterized all five logic cells directly from their current extracted
SPICE, without changing CELLS. The five schema-2 tables live at
`results/sta/propagation/tables/<CELL>.propagation.json`:

- **150 profiles / 6,840 directed observations, all nominal band checks pass.**
- Loads: 10, 100, 500, 1000, 2000 fF. Full ramps: 0.25, 1, 5, 15, 50, 150 ns.
- `propagation_s = t50(output) - t50(input)`, with the midpoint between the
  actual old/new ideal levels. It is −2.5 V for −1→0 and 0 V for −1→+1.
  Last directional crossings are used and crossing counts retained. Signed
  propagation is allowed; it is never clamped to a positive delay.
- `output_slew_10_90_s = t90 - t10`; receiving full ramp = output slew / 0.8.
- `tail_s = final entry into the ideal ±0.5 V band - t50(output)`.
  **Only propagation composes; the tail is added once at the output.**
- Endpoint-stable arcs retain measured scalar recovery; no fictitious midpoint
  or slew is assigned to them.
- Every profile keeps the real deck, log, measurement and model/code hashes.
  Representative waveforms are compressed. Earlier finer-step/longer-plateau
  observations retain their original provenance when reused. CELLS timing,
  extraction and model hashes/generation are checked on load. No circuit-level
  data is used to fit the tables.

The event model orders reconvergent pin midpoints, selecting measured single-pin
arcs with their intermediate side-input trits. Equal-time changes use the
synchronous multi-pin observations. Logical pulses can traverse nets whose
whole-vector endpoints are unchanged. A reversed request before the pending
output midpoint suppresses that pulse. Overlapping ramps, cancelled pulses,
unpropagated local analog hazards and time-order clamps are counted. A clamp's
contribution is explicit in `PathStage.time_order_adjustment_s`; subtract it
from `delay_s` to recover the sampled propagation delay. This is an event
approximation, not an analog transient solver.

The global graph still provides transition-specific arrivals, exact joint
settled endpoint sensitization, cell-by-cell paths and full primary-input
patterns, using a fixed requested ramp. `analyze(..., vector_pairs=pairs)`
selects the new slew/event mode. Its path pin states describe timed intermediate
values, rather than necessarily the whole-vector endpoints at every stage.
No global analog worst-case bound is claimed by either model.

Interpolation is bilinear in physical load/ramp units. Cell sampling is strict.
The graph's explicit `linear` load policy can extend to zero or twice the
largest measured load; `load_policy="error"` forbids it. Event analysis clips
an equivalent ramp to the tested axis if necessary and records that action.
Failed/null samples are rejected. The present 39-output load comparison fits
within the new measured load axis; no load extension is needed.

## Validation and ablations

Every comparison uses the same maximum biased device pin C, 10 fF output test
loads, and SIM's exact LVS-mapped top-net GDS C, including connected terminal
metal once. The public PNR-only estimator supplies merged route/pin C and omits
cell terminal metal; it is a distinct, documented approximation.

| Model on the SIM endpoint pairs | MAPE | Within ±20% |
|---|---:|---:|
| Phase 1: additive band settling | 70.31% | 0 / 39 |
| Midpoint + endpoint tail, fixed ramp | 35.91% | 2 / 39 |
| Midpoint + propagated slew, synchronous endpoint classes | 10.30% | 30 / 39 |
| Ordered midpoint events + endpoint tail | **6.78%** | **38 / 39** |

The phase-1 reference uses its original table grid; the new surfaces extend load
coverage to 2 pF. These are successive engineering comparisons, not a fitted
partition of error among independent factors. JSON retains all per-output
values for every model and signed empirical error extrema.

The following times are maxima over outputs (ns); the last column checks each
individual output and therefore exposes exceptions hidden by a design maximum.

| Design | SPICE maximum | New estimate maximum | Largest individual output error |
|---|---:|---:|---:|
| scaling/adder1 | 139.90 | 139.94 | 12.23% |
| scaling/adder2 | 142.54 | 160.11 | **36.48%** |
| scaling/adder3 | 169.46 | 184.19 | 15.79% |
| scaling/adder4 | 231.81 | 221.24 | 15.69% |
| scaling/adder5 | 286.55 | 278.19 | 16.00% |
| scaling/adder6 | 343.68 | 333.83 | 7.88% |
| example/adder4 | 231.80 | 221.24 | 19.30% |
| example/full_add | 108.63 | 111.20 | 2.36% |
| example/mac1 | 147.56 | 138.89 | 7.90% |
| example/mul1 | 17.14 | 17.02 | 0.70% |

The only target miss is **scaling/adder2 `cout`: 143.79 ns predicted versus
105.36 ns observed worst**, +36.48%. Its predicted worst `opposite_operands`
pattern actually settles in **14.72 ns**. A complete original-sequence replay
with internal probes is retained under `diagnosis/adder2/`; `outlier.json`
records each predicted transition and the actual directional crossings.
Already at `digit[0].fa.ha1.g_c`, the model assumes a +1→0 transition, but the
observed node remains approximately **−5.05 to 0 V** and never crosses +2.5 V.
Several subsequent predicted full-level transitions likewise do not occur.
The model turns overlapping partial-voltage activity into full trit events and
therefore creates a false late carry path. Changing a scale factor cannot fix
that mechanism. Meeting ±20% on this case needs partial-pulse amplitude,
relative-arrival/skew and overlapping waveform characterization or an analog
macromodel. The exception remains visible; `accuracy_passed` is false.

50 ps controls at 100 fF / 1 ns are retained under `results/sta/resolution/`.
Maximum midpoint differences are **1.43 ps (INV)** and **19.81 ps (NANY)**;
endpoint-tail differences are 1.94/13.84 ps. This is a spot check, not a bound
across the entire grid or on circuit glitches. Primary runs use at most 250 ps
steps (some reused profiles are finer), with at least a 250 ns plateau after
each full ramp. Neither the table nor empirical error range covers PVT,
calibrated signal/poly RC, coupling, package effects or arbitrary analog history.

## API, reproduction and notebook handoff

```python
from tritflow.sta import analyze
from tritflow.sta.plot import validation_figure

pairs = [({"a": -1, "b": 1, "cin": 1},
          {"a": 0, "b": -1, "cin": -1})]
r = analyze("build/full_add/full_add.json", "build/full_add/full_add.pnr.json",
            vector_pairs=pairs)
print(r.arrival, r.sensitizing_pattern)
r.to_html("results/sta/full_add.html")
validation_figure().show()
```

`PropagationLibrary` is the default; explicitly passing the original
`TimingLibrary` keeps the historical additive model. Pattern flags
`ordered_events=False` and `propagate_slew=False` reproduce the ablations.
Validation obtains every pair from the current SIM measurement/vector files.
It checks current source hashes, pinned provenance, all consumed physical
snapshots and all foreign `results/` content, and retries changed publications.
The STA table files and imported-code hashes also participate. Optional watch
mode repeats on later changes and reuses only content-matching design caches.

```sh
python3 -m pytest tests/sta -q
python3 -m tritflow.sta.validate
python3 -m tritflow.sta.validate --watch-seconds 600
python3 -m compileall -q tritflow/sta tests/sta
# Offline characterization / evidence reproduction:
python3 -m tritflow.sta.characterize --jobs 2
python3 -m tritflow.sta.characterize --resolution
python3 -m tritflow.sta.diagnose build/full_add --step-ns 0.25
python3 -m tritflow.sta.diagnose build/adder_scaling/adder6 --name adder6
python3 -m tritflow.sta.diagnose --audit
```

Cached pattern timing takes at most about **35 ms/design** in the recorded
validation. Exact global endpoint search reached 15.9 s for N=6 while other
verification jobs shared the machine. These are measured host-dependent times;
no SPICE is started by the analysis/plotting/validation readers.

Integrator/FRONTEND handoff: include the five midpoint JSON tables under
`results/sta/propagation/tables/` in the existing Colab data fetch (about 2.52 MB,
plus the already-required CELLS timing/extraction files). Characterization runs,
diagnostic waveforms and charge experiments are not runtime assets. Chapter 7
should identify the 38/39 finite-pattern accuracy and the single documented
exception; the API's fixed-ramp global search has a different model scope.

## Remaining limits / interface requests

The strict all-39 ±20% accuracy target is not met. The one failure mechanism is
probed and documented above; no unavailable waveform precision is claimed.
No CELLS/SIM/PNR API or publication change is required. All new electrical
tables and evidence are under STA ownership. No external messages were sent.
The final source-content and STA-code fingerprints match the saved validation;
no STA background process or watcher remains running.
