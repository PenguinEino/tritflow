# Ternary static timing

`analyze` uses measured midpoint propagation and an endpoint-only settling tail.
No SPICE is launched by analysis, plotting or validation; characterization is a
separate offline producer. Without `vector_pairs`, the default is a conservative local-class/ramp envelope.
It considers independently every measured transient class and internal ramp,
propagates a recovery guard on endpoint-stable nets, and adds the final tail
once. Supply complete `vector_pairs` for matched slew/event timing. The exact
fixed-ramp endpoint graph remains available as `global_mode="endpoint"`.

```python
from tritflow.sta import analyze
from tritflow.sta.plot import validation_figure

report = analyze("build/full_add/full_add.json",
                 "build/full_add/full_add.pnr.json",
                 vector_pairs=[({"a": -1, "b": 1, "cin": 1},
                                {"a": 0, "b": -1, "cin": -1})])
print(report.arrival)                 # output -> settling estimate in seconds
print(report.sensitizing_pattern)     # complete primary-input endpoints
for stage in report.critical_path:
    print(stage.instance, stage.input_transition, stage.output_transition,
          stage.delay_s, stage.settling_tail_s)
report.to_html("results/sta/full_add.html")
validation_figure().show()
```

The example checks one endpoint pair. The validation command uses every
consecutive pair from each of SIM's ten complete vector sequences.
GateNetlist objects/dicts and PnrResult objects are also accepted. Fanout load
sums each connected pin's maximum published biased AC input C, plus merged
route/external-pin C from the public extraction API. With no PNR, load is fanout
only. External output load defaults to 10 fF; `output_load_f` accepts a scalar
or output-name dict. `wire_caps={logical_net: farads}` overrides route C. The
validation uses SIM's exact LVS-mapped full top-net metal C, including connected
cell terminal metal once; the public route-only estimate excludes that metal.

The measured quantities for each directed old/new trit pair are:

```
p50 = t50(output) - t50(input)
slew = t90(output) - t10(output)
tail = final_band_entry(output) - t50(output)

next_t50 = input_t50 + p50
endpoint_settling = endpoint_t50 + endpoint_tail
next_full_ramp = output_slew / 0.8
```

Only `p50` composes through intermediate stages. Each stage starts moving before
its input has fully settled. The midpoint is between the old and new ideal
levels: −1→0 crosses −2.5 V; −1→+1 crosses 0 V. The last directional crossing is
used, with crossing counts retained. Negative midpoint propagation is allowed
when the output crosses before the selected input's midpoint. The tail is added
once, at the observed endpoint, rather than at every gate.

STA-owned schema-2 surfaces are under `results/sta/propagation/tables/`: five
cells, 150 load/ramp profiles, 6,840 directed observations. Loads are
10/100/500/1000/2000 fF; full input ramps are 0.25/1/5/15/50/150 ns. All profiles
pass nominal ideal ±5/0 V band checks. Extracted device models, model hashes and
cell generation must match the current CELLS publication. The isolated
characterization uses existing public SIM APIs and Newton initial guesses;
no voltage is forced during transient analysis. CELLS/SIM files are read only.
Every profile retains its deck, log and measurements; representative waveforms
are compressed. Earlier finer-step/longer-plateau observations retain their
original provenance when reused. No circuit-level timing fit is applied.

Interpolation is bilinear in physical load/ramp units. Strict cell sampling
never crosses failed/null points. `analyze` defaults to explicitly reported
linear load extension down to zero or up to twice the largest measured load;
use `load_policy="error"` to forbid load extension. Pattern analysis clips
an out-of-domain equivalent ramp to the measured boundary and reports it.
It does not extrapolate a ramp silently. These policies do not establish bounds.

Pattern analysis orders input midpoint events, using measured single-pin arcs
with the intermediate side-input trits. Equal-time changes use synchronous
multi-pin observations. Output slew supplies the next equivalent ramp. Logical
pulses can traverse nets whose final endpoint values are unchanged. A reversed
request before a pending output midpoint suppresses that pulse; overlapping
ramps, pulse cancellations, unpropagated analog hazards and time-order clamps
are counted. Any clamp is also explicit in the path stage's
`time_order_adjustment_s`; subtract it from `delay_s` to recover the sampled
propagation delay. This is a timing-event approximation, not an analog solver.
Paths in this mode contain timed intermediate states, which need not equal
all internal nets' whole-vector endpoints. Partial pulse amplitude and arbitrary
skew/shape require additional characterization.

The diagnostic fixed-ramp endpoint graph retains separate transitions and every predecessor. Reduced
ternary decision diagrams intersect path conditions; best-first backward search
rejects incompatible reconvergence. Its critical endpoint pattern is jointly
sensitizable in settled logic. Fixed-ramp global timing is a distinct model
from the tested-pattern event analysis and is not a global analog bound.
Resource limits raise rather than return partial success.

Phase 3 corrects the unsafe interpretation of the old global estimate. It
underpredicted 35/39 maxima (down to −38.47%). The isolated tables already
contain every six/72 directed local class. The problem was discarded slew and
transient classes excluded by settled endpoint constraints. Relaxing those
constraints at the same 1 ns ramp leaves eight underpredictions (down to
−11.87%), so class coverage alone is insufficient. Maximizing local midpoint
and endpoint-tail terms over the measured internal ramp knots removes all
underpredictions. The recovery clock adds protection for downstream activity
on nets that return to their original level. Actual loads are unchanged.

The new default `predicted_s` is conservative against **all 838 saved output
observations (799 transitions)**, covering all 39 maxima. It is deliberately
pessimistic: **4.52–8.50×**, mean **6.02×**, the measured maximum (+351.89% to
+750.08%). Every term comes from independent isolated-cell SPICE; there is no
circuit fit, simulated-value floor or fitted multiplier. Known primary ramps
remain 1 ns; internal ramps range across all measured knots. The endpoint tail
uses the same local class and ramp as its propagation term, and is added once.
The maximizing local classes are independent, so no jointly sensitizing vector
is asserted for an envelope path. `global_mode="endpoint"` still provides a
joint settled-endpoint witness when that diagnostic is needed.

This establishes conservatism on the saved nominal dataset, not an analog
signoff guarantee. All-class output slew can exceed the 150 ns input-ramp axis;
reports explicitly flag non-closed domains, without silently clipping a bound.
Arbitrary partial pulses, unequal multi-input ramps, waveform history, PVT and
wire/poly RC remain outside the scalar characterization. Tighter useful global
bounds need class-correlated slew and skew/pulse characterization; claiming
that accuracy from this deliberately relaxed envelope would be misleading.
`worst_case_conservative` is the finite-dataset coverage flag;
`certified_analog_bound` remains false. The same 39 matched results below are
unchanged and are the only accuracy claim.

Validation covers the same 39 outputs as phase 1: **38 within ±20%**, MAPE
**6.78%**, signed error **−7.90% to +36.48%**. The remaining scaling-adder2
`cout` estimate is 143.79 ns versus the sequence's observed maximum 105.36 ns.
The predicted worst pattern actually settles in 14.72 ns: internal probing
shows that a modeled intermediate +1 level never occurs. Its waveform stays
between roughly −5 and 0 V and does not cross +2.5 V. Full-level event timing
therefore propagates a false late transition. Accurate treatment requires pulse
amplitude and overlapping-input waveforms. `accuracy_passed` remains false;
this outlier is retained, and no fitted correction is applied.

The successive comparisons are archived: additive settling MAPE 70.31%;
midpoint composition with fixed ramp 35.91%; midpoint with propagated slew but
synchronous endpoint classes 10.30%; ordered midpoint events 6.78%. Phase-1
reports remain in `results/sta/phase1/`; the complete phase-2 publication is
archived in `results/sta/phase2/`. The default validation figure shows the
matched-pattern event estimates and ±20% reference lines; the conservative envelope
trace is available in the legend. `pessimism_figure()` and
`results/sta/pessimism.html` show envelope / measured maximum separately. Empirical error ranges apply only to the
finite nominal dataset. No PVT, calibrated wire/poly RC, coupling or package
claim is made. A finite-transition input-charge experiment was not adopted:
signed multi-terminal charge does not justify replacing pin C with a positive
lumped capacitor inferred from those samples.

```sh
python3 -m tritflow.sta.validate
python3 -m tritflow.sta.worst_audit
python3 -m tritflow.sta.validate --watch-seconds 600
python3 -m pytest tests/sta -q

# Offline producers; never needed for cached notebook reads:
python3 -m tritflow.sta.characterize --jobs 2
python3 -m tritflow.sta.characterize --resolution
python3 -m tritflow.sta.diagnose build/full_add --step-ns 0.25
python3 -m tritflow.sta.diagnose build/adder_scaling/adder6 --name adder6
python3 -m tritflow.sta.diagnose --audit
```

`PropagationLibrary` loads the new surfaces. An explicitly supplied legacy
`TimingLibrary` retains additive settling for comparison. Pattern flags
`ordered_events=False` and `propagate_slew=False` select the block and fixed-ramp
ablations. Published validation fingerprints all foreign results, consumed
physical evidence, current cell tables, the STA propagation tables and imported
STA code. A changed publication triggers retries; watch mode repeats on later
changes. No foreign producer is started or stopped. Cached design calculations
are invalidated by consumed-content changes, including unchanged timestamps.
