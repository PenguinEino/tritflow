# Ternary static timing

```python
from tritflow.sta import analyze
from tritflow.sta.plot import validation_figure

report = analyze("build/full_add/full_add.json",
                 "build/full_add/full_add.pnr.json")
print(report.arrival)                 # output -> seconds
print(report.transition_arrival)      # output -> directed trit pair -> seconds
print(report.sensitizing_pattern)     # complete before/after primary-input dicts
for stage in report.critical_path:
    print(stage.instance, stage.cell, stage.input_transition,
          stage.output_transition, stage.delay_s)
report.to_html("results/sta/full_add.html")
validation_figure().show()
```

GateNetlist objects/dicts and PnrResult objects are also accepted. No SPICE
process is started by analysis or plotting. Passing no PNR uses fanout C only.
`wire_caps={logical_net: farads}` overrides route C, useful for LVS-mapped full
GDS capacitances. External output load defaults to 10 fF; use `output_load_f`
as a scalar or an output-name dictionary to override it. Fanout C sums each
connected pin, including two pins on the same cell when both connect to a net.
The maximum biased device input C is deliberately conservative. Full-GDS C
already includes connected terminal metal; no separate cell metal is added.

Cells are read from the current `cells/out` publication, with generation and
extracted-source hash checks. `TimingLibrary(cells, root=...)` supports private
snapshots. All published single-pin and simultaneous endpoint transitions are
available through `library[cell].arcs`; `sample(arc, load_f, ramp_s)` interpolates
their measured settling surfaces. Legacy `.char.json` sequences do not cover
all directed arcs and cannot silently replace a missing `.timing.json`.

The graph retains separate states for each of six changing trit transitions,
and local unchanged-output recovery. Each gate requires the exact before/after
values of every input pin. A symbolic ternary decision diagram intersects these
requirements with preceding path conditions. A best-first search starts with
graph arrival upper envelopes and finds the slowest path whose settled endpoint
conditions are jointly satisfiable. Alternate paths remain available after a
faster feasible path displaces an infeasible graph winner. The reported complete
input pattern realizes every listed cell condition, including reconvergence and
tied inputs. No random vector sampling or beam pruning is used. Resource limits
raise rather than return incomplete success.

The numerical model adds cell settling times along that path, using a fixed
full linear input ramp at every stage (1 ns by default). It does not propagate
slew, waveform shape, skew or an intermediate glitch whose settled endpoints
are unchanged. Local unchanged-output recovery is included in output maxima,
but cannot substitute for a waveform model for cascaded hazards. Simultaneous
tables were characterized with equal synchronous ramps. The endpoint witness
proves logical consistency, not analog delay realization. Constant nets have
zero transition arrival; this does not estimate power-up or tie-rail settling.
The estimate can be strongly pessimistic and **is not a certified timing bound**.

Interpolation is bilinear in physical load/ramp units. The current measured
domain is 5 fF–1 pF and full ramps 1–150 ns. `CellTiming.sample` is strict by
default. `analyze` defaults to explicitly reported linear load extension because
some real adder fanouts exceed 1 pF: use the two nearest columns down to zero or
up to twice the largest measured load, floor negative extrapolated values at
zero, and list every affected instance in `report.warnings`. No ramp extension
is allowed, and no failed/null sample with nonzero interpolation weight is used.
Use `load_policy="error"` for strict graph analysis. Load extension is an
uncharacterized estimate; it provides no accuracy or monotonicity guarantee.

Reproduce the ten-design comparison without modifying SIM/PNR artifacts:

```sh
python3 -m tritflow.sta.validate
python3 -m tritflow.sta.validate --watch-seconds 600
python3 -m pytest tests/sta -q
```

Validation uses the six real scaling adders and four example simulation
snapshots, the same 10 fF test loads, and SIM's full top-net GDS capacitance
mapped through its strict LVS cross-reference. It writes reports, per-output
errors and empirical signed error ranges to `results/sta/validation.json`, plus
an interactive comparison in `results/sta/validation.html`. `qualified_current`
describes source freshness/pinned provenance; `accuracy_passed` is null because
no accuracy acceptance threshold is specified. Inspect the error statistics.

All-endpoint STA and STA restricted to SIM's actual consecutive vector pairs
are reported separately. The first has broader endpoint coverage than SIM;
the second exposes electrical approximation error on matching endpoints.
Neither recreates SIM's internal analog histories. Recorded error extrema apply
only to the finite nominal dataset, not untested designs, loads or PVT.

The producer fingerprints all foreign `results/` files, timing/source tables,
and consumed physical evidence before/after validation. Changed publications
cause retries; watch mode repeats on subsequent changes. A stale/running SIM
result is recorded explicitly and never marked qualified. Actual content hashes
are compared rather than timestamps. No foreign producer is started or stopped.
