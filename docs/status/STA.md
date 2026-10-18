# STA stream — phase 4 complete: tighter bound; 1.5× target not achieved

2026-10-18. Only STA-owned paths changed. No packages installed, PDK/reference
edits, foreign producer/process changes or git-state mutations. Qualification
remains public PDK `5d963db9d44e192d37a0489c208bfccf2e2f690c` and CELLS generation
`2026-10-18T10:26:47.211617+00:00`. Phases 1–3 are archived separately.

## Result and target status

The new default uses **measured transition/slew windows with compatible source
conditions**. It covers **838/838 saved observations (799 transitions)** with
**zero underpredictions**, while reducing bound / measured maximum from
**4.519–8.501×, mean 6.016×**, to **1.026–3.072×, mean 2.182×** (median 2.370×).
The mean factor is **63.7% smaller**. Absolute overestimates now range from
**0.408 ns to 457.24 ns**.

The requested **1.5× target is not met**: only **2/39 outputs** lie between 1×
and 1.5×. The schema-4 publication explicitly records
`bound_target_passed:false`, `bound_target_factor:1.5`, and
`bound_outputs_within_target:2`. No observation was dropped and no empirical
multiplier, circuit-derived floor, delay cap or C correction was introduced.

**Matched accuracy is unchanged bit for bit:** **38/39 within ±20%, MAPE
6.782%, MAE 10.479 ns**, signed error −7.903%…+36.479%. Scaling adder2 `cout`
remains the phase-2 partial-pulse exception. `tested_predicted_s` is the only
accuracy claim. The new `predicted_s` is a conservative comparison against the
saved nominal dataset; **`certified_analog_bound:false`** remains explicit.

**35 STA tests pass**, final run **23.11 s**. Current validation refreshes all
ten designs and compares every saved output observation. The separate phase-4
audit verifies producer/code fingerprints, unchanged loads, unchanged matched
predictions, unchanged old table rows and exact diagnostic circuit identity.

## What dominated phase 3

`results/sta/phase4/attribution.json` reproduces a full 2×2×2 experiment using
the archived 150 ns-axis tables and identical loads. The factors are arbitrary
internal ramp range, propagated recovery activity, and the endpoint tail.
Order-independent Shapley attribution (all six application orders) of the
increase over fixed-1-ns/no-guard/no-tail timing is:

| Factor | Mean added time | Share of relaxation increase |
|---|---:|---:|
| Broad internal ramp envelope | **794.74 ns** | **95.34%** |
| Propagated recovery activity | 21.51 ns | 2.58% |
| Endpoint tail | 17.31 ns | 2.08% |

Even removing **both recovery propagation and the endpoint tail** from the
broad-ramp model leaves factors **1.175–7.799×**. Tail/guard trimming alone
therefore cannot approach the target. Dropping tails is also physically wrong:
a direct output still needs its measured time from midpoint to the ±0.5 V band.

## Measured terms replacing the broad relaxation

`tritflow/sta/window.py` now carries each output transition with a **5 ns-wide
full-ramp interval**. Measured output 10–90% slew / 0.8 transports that interval
to the receiving gate. Input knots and inverse output-bin crossings split the
piecewise-linear surfaces. Different transition histories no longer share an
arbitrary 150 ns ramp, and delay/slew correlations are retained within each
narrow segment. Backward symbolic search intersects the complete path's
primary-input compatibility instead of splicing incompatible source histories.
Transient side-input values are admitted, including endpoint-stable logical
pulses, but relative time and partial pulse amplitude are still relaxed.

The endpoint term maximizes **d50 + tail on the same segment**, then subtracts
the segment's d50 maximum to obtain the residual added once at the endpoint.
It does not splice independent maximum d50 and maximum tail from unrelated
conditions. Intermediate tails remain uncounted in composed arrival; path
fields retain local endpoint data for inspection.

Recovery is kept as the **measured local scalar band-recovery term**. It is
never turned into a fictitious full-level crossing or a made-up output slew
and repeated downstream. Representative saved waves at 100 fF / 1 ns show
why duration is insufficient: stable-output NANY classes peak at **1.966 V**
from their ideal level (none cross a 2.5 V half-level), while NAND/NOR include
larger partial pulses (maxima **3.145/3.103 V**). These observations are scoped
to that profile; they do not justify dropping analog propagation generally.
Full-level logical pulses are represented through transient classes; propagation
of **partial analog recovery remains explicitly unmodeled**. Zero misses are
established on all 838 observations, not asserted for arbitrary pulse shapes.

Some class-conditioned slew ranges reached 154–157 ns, beyond the old table
axis. Phase 4 independently measured **25 additional profiles at 200 ns**, all
passing. The five tables now contain **175 profiles / 7,980 observations**.
Every original row is unchanged, and extraction/model/generation identities
still match CELLS. Every used internal slew label in the current analysis fits
the measured domain. **Out-of-domain labels raise instead of being clipped.**
No load extension is needed. The old phase-3 tables are preserved under
`results/sta/phase3/propagation_tables/` for exact attribution reproduction.

## Why the remaining gap cannot be justified away with these data

The controlled model comparisons on the same 39 maxima are:

| Model | Factor range | Mean factor | Missed saved observations |
|---|---:|---:|---:|
| Phase 3, broad ramp/recovery relaxation | 4.519–8.501× | 6.016× | 0 |
| Narrow transition/slew labels, unconstrained side states | 1.026–3.084× | 2.201× | 0 |
| Source-compatible transient classes (new default) | 1.026–3.072× | 2.182× | 0 |
| Settled endpoint classes only (rejected) | 0.981–1.831× | 1.351× | **3** |

The three endpoint-only misses are scaling adder1 `sum[0]`, scaling adder3
`sum[0]`, and example mac1 `cout`. Restricting classes just because that tighter
model averages below 1.5× would restore measured underprediction.

1. **Numerical bin width is not the main remaining error.** For adder2 `cout`,
   endpoint-window timing is 192.88 ns at 5 ns bins, 186.86 ns at 1 ns bins,
   and **185.85 ns at 0.25 ns bins**. The last refinement changes it by only
   **1.01 ns**. The same selected vector's synchronous block estimate is
   **185.80 ns**, so the scalar cell model itself converges above the target.
2. **An unseen physical transition almost exhausts a 1.5× ceiling already.**
   A SPICE replay of that model-selected vector uses the **exact published
   adder2 network, device/wire/output C, supplies and 1 ns ramps**; only the
   stimulus sequence/hold/sampling changes. `cout` settles in **152.35 ns**,
   versus the original seven-vector maximum **105.36 ns**: **1.446×**. Only
   **5.68 ns** remains below the requested 1.5× ceiling. This replay is separate
   diagnostic evidence and does not silently replace the 838 observations.
3. **The missing information is waveform/timing history.** On that same
   vector, matched ordered-event timing is **172.48 ns** (**20.13 ns high**),
   and finest-bin endpoint-window timing is **185.85 ns** (**33.50 ns high**).
   Equal-ramp isolated-cell tables do not distinguish unequal pin slopes,
   relative skew, partial pulse amplitude, or charge left by overlapping
   transitions. Reachable side levels need not be present at the same time.
   Full-level pulse assumptions admit late transitions that never reach their
   assumed voltage. Neither smaller scalar bins nor a trimmed final tail can
   bound these effects to the remaining 5.68 ns without new information.

**This is not a proof that a physical 1.5× bound is impossible.** It is a
specific failure to justify or achieve it with the present scalar measurements.
A tighter global model needs joint arrival/slew/history constraints plus
measured two-input skew and pulse-width/amplitude responses (and retained
internal waveforms). Fitting a percentage or clipping to the finite sequence's
observed maxima would conceal the gap. Those shortcuts are not adopted.

The minimum nominal slack is only **0.408 ns**, while some source sequences
use 2 ns sampling. Finite-grid observation coverage, even with all used scalar
slews characterized, is not analog signoff margin. PVT, signal/poly RC,
waveform history and arbitrary analog hazards remain outside qualification.

## Artifacts, API and integrator handoff

- `results/sta/validation.json`: schema 4, all 838-case coverage, explicit failed
  1.5× target, separate matched accuracy and current provenance.
- `results/sta/phase4/audit.json`: source/code checks, component attribution,
  candidate failures, unchanged-load/table/matched checks and SPICE witness.
- `results/sta/phase4/tightening.html`: all 39 old/new factors and a 1.5× line.
  Root `validation.html` and `pessimism.html` are refreshed as well.
- `phase4/attribution.json`, `windows.json`, `bin_convergence.json`: reproducible
  numerical experiments. `phase4/exact_witness/` and `phase4/witnesses/` retain
  diagnostic decks, logs, measurements and waveforms. Additional carry/random
  candidates are separate from the original validation set.
- `analyze()` defaults to `global_mode="windows"`. `global_mode="endpoint"`
  retains fixed-ramp settled-endpoint timing; `global_mode="envelope"` retains
  the broad relaxation over the current table axis. Explicit legacy libraries
  and matched `vector_pairs` behavior remain available.
- Default paths have compatible primary endpoints, **not a joint temporal
  waveform witness**. `before/after:null` and a reason prevent a false
  sensitization claim; `compatible_primary_endpoints` records the constraints.

```sh
python3 -m tritflow.sta.validate
PYTHONPATH=. python3 results/sta/phase4/audit.py
python3 -m pytest tests/sta -q

# Optional exact reproductions:
PYTHONPATH=. python3 results/sta/phase4/attribute.py
PYTHONPATH=. python3 results/sta/phase4/windows.py
PYTHONPATH=. python3 results/sta/phase4/exact_witness.py
```

**Interface request / handoff:** show the improved 1.03–3.07× nominal bound and
its failed 1.5× target honestly. Keep `tested_predicted_s` as the accuracy claim.
Further CELLS/SIM waveform/skew characterization would support another step;
no shared interface or foreign stream file was edited. No question or approval
is pending. The investigation and tighter publication are complete; the
remaining 1.5× accuracy/conservatism gap is documented above.

---

# STA stream — phase 3 complete: conservative nominal envelope, accuracy kept separate

2026-10-18. Only STA-owned paths changed; no packages installed, foreign
producer/process changes, PDK/reference edits or git-state mutations.
Qualification remains public PDK `5d963db9d44e192d37a0489c208bfccf2e2f690c`,
CELLS generation `2026-10-18T10:26:47.211617+00:00`.

## Result and what can be claimed

The new default **`predicted_s` exceeds all 838/838 saved output observations**,
including **799 transition observations**, across the same ten designs and
**39 outputs**. No startup, unchanged-output glitch or individual transition
is omitted. There are **zero underpredictions**. The schema-3
`results/sta/validation.json` is `complete:true`, `qualified_current:true`,
`stable_snapshot:true`, `worst_case_conservative:true`.

The envelope is very pessimistic: **4.5189–8.5008×** the measured per-output
maximum (**+351.89% to +750.08%**), mean **6.0161×**, median **6.2744×**.
Absolute overestimates range from **56.21 ns to 1743.72 ns**. It is an
independent measured-domain envelope, not a useful accuracy estimate. No
circuit-derived floor, fitted multiplier or correction to pin C is used.

**Matched-event accuracy is unchanged bit for bit on all 39 outputs:**
**38/39 within ±20%, MAPE 6.782%, MAE 10.479 ns**, signed errors
**−7.903% to +36.479%**. `accuracy_passed:false` remains correct for scaling
adder2 `cout`; its phase-2 partial-pulse explanation still applies. This is the
only accuracy claim. The old global graph is no longer described as an analog
worst case.

**30 STA tests pass**, final run **19.94 s**. Validation and the diagnostic audit
both checked the current source fingerprint; STA code hashes match the executed
source. Re-run-on-publication-change behavior remains intact. No watcher or
simulation process is left running.

## Diagnosis

The reproducible `results/sta/diagnosis/phase3_audit.json` checks every local
class, compares loading and matched results with the preserved phase-2 reports,
and identifies the actual maximum observation's vector and endpoint class.

| Analysis, same loads and SIM maxima | Underpredicted outputs | Signed error range |
|---|---:|---:|
| Previous fixed-1-ns, jointly sensitized endpoint graph | 35/39 | −38.47% … +26.64% |
| All independent transient local classes, still 1 ns | 8/39 | −11.87% … +64.70% |
| Independent classes and all internal ramp knots | 0/39 | +329.72% … +726.75% |
| Plus propagated unchanged-output recovery guard (default) | 0/39 | +351.89% … +750.08% |

1. **The tables have no missing directed local endpoint class:** six each for
   INV/BUF and 72 each for NAND/NOR/NANY, every measured knot passing. What was
   missing was *transient reachability*: exact jointly settled PI endpoint
   constraints reject local classes that can occur at different times in a
   reconvergent pulse. Three measured output maxima have unchanged endpoints:
   scaling adder1 `cout`, full_add `sum`, mac1 `sum`. Stable recovery formerly
   terminated at its own gate instead of being allowed to drive downstream
   activity. Relaxing classes removes most, but not all, underpredictions.
2. **Global slew was discarded.** The previous graph sampled every gate at a
   full 1 ns ramp even though phase-2 SPICE probes measured equivalent internal
   ramps up to 88.35 ns. Its `output_slew_10_90_s` fields were sampled but did
   not affect its global recurrence. Large-load and slow transition classes
   need different d50 values. Sampling the same actual load across the measured
   internal ramp axis removes the remaining underpredictions.
3. **Tail placement was correct, tail conditions were too narrow.** There is
   no missing tail term to add to each stage. The endpoint tail was added once,
   but at 1 ns. For example, the new adder6 `sum[0]` envelope endpoint class
   NANY:67 at 97.03 fF has a 31.24 ns tail at 150 ns versus 15.33 ns at 1 ns.
   The new envelope keeps d50 and tail on the same local class/ramp, adding the
   tail once. Intermediate tails are not stacked.
4. **Loading has not changed.** Every per-net fanout/wire/external load equals
   phase 2. All present loads fit the measured 10 fF–2 pF axis. This rules out
   an unrecorded C-model correction as the explanation for the new coverage.

## Implementation and decisions

`tritflow/sta/envelope.py` computes a monotone activity-clock recurrence over
the DAG. For every active input pin, local class and measured internal ramp,
it considers parent clock + d50 for changing outputs or parent clock + recovery
for unchanged outputs. Both can propagate as activity clocks. At an endpoint,
changing candidates add their own tail; recovery candidates need no tail.
Known primary ramps remain 1 ns. Piecewise-linear ramp interpolation has its
maxima at the knots, so all internal knots are considered without clipping.
The same scalar recurrence covers pulses that return to an unchanged endpoint.

Maximizing local classes and ramps independently admits false paths and
incompatible slow conditions. That deliberate relaxation explains the large
pessimism. Paths show the actual maximizing table terms, but **no jointly
sensitizing PI vector is invented** (`patterns.before/after:null` with reason).
`analyze(..., global_mode="endpoint")` retains the exact endpoint-witness
graph as an explicitly limited diagnostic. `vector_pairs=...` retains the
unchanged matched event model. Legacy explicit `TimingLibrary` behavior is
also unchanged. No foreign table needed modification; the phase-2 isolated
SPICE surfaces already characterize these local classes and ramps.

The finite-dataset conservatism flag is deliberately separate from a universal
analog guarantee: **`certified_analog_bound:false`**. All-class output-slew
upper limits exceed the 150 ns input axis at some pins in nine designs (407
pin occurrences total); these non-closed domains are explicit in every report
and validation. They are neither silently clipped nor claimed qualified.
Arbitrary pulse amplitudes, unequal ramps/skew/history, PVT and signal/poly RC
remain outside the scalar characterization. Tighter globally useful bounds
require class-correlated slew and skew/pulse characterization. No blocker
remains for the requested conservative comparison against every saved case.

## Artifacts, notebook handoff and checks

- `results/sta/validation.json`: schema 3, coverage for every saved case,
  pessimism, matched accuracy, four global diagnostic ablations and provenance.
- `results/sta/validation.html` / `validation_figure()`: matched accuracy shown
  by default, conservative envelope available as a separate optional trace.
- `results/sta/pessimism.html` / `pessimism_figure()`: 39 envelope / SPICE factors,
  separate from the accuracy chart.
- `results/sta/diagnosis/phase3_audit.json`: complete class coverage, same-load
  checks, unchanged matched estimates, actual maximum vectors and tail samples.
- Twenty refreshed root timing reports; full phase-2 publication preserved at
  `results/sta/phase2/`, and phase 1 remains at `results/sta/phase1/`.

```sh
python3 -m tritflow.sta.validate
python3 -m tritflow.sta.worst_audit
python3 -m pytest tests/sta -q
```

New tests cover slow internal classes, exactly one tail, downstream recovery
activity, rejected failed samples, out-of-domain primary ramps, explicit
non-closed slew domains, constant cones, and per-case validation of stable
hazards and missing observations. Earlier phase-2 tests continue to pass.

**Interface request / integrator handoff:** chapter 7 should use
`tested_predicted_s` for the 38/39 accuracy claim and label `predicted_s` as the
conservative nominal envelope, reporting its 4.52–8.50× pessimism and the
non-certified scope. No shared interface file was edited.

---

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
