# Simulation API

The harness uses the installed TR-1um models and ngspice. All input/expected
values are trits (-1, 0, +1); loads are farads, all times seconds. Returned
waveforms are numpy arrays in plain dictionaries. `simulate` retains no files
unless `workdir` is supplied.

```python
from pathlib import Path
from tritflow.sim import input_vectors, simulate, dc_transfer
from tritflow.sim.characterize import characterize_cell

spice = Path('cells/out/NANY/NANY.ext.spice').read_text()
expected = lambda v: {'Y': -max(-1, min(1, sum(v)))}
result = simulate(spice, 'NANY', ['A', 'B'], ['Y'],
                  input_vectors(2, transitions=True), expected,
                  loads_f=100e-15, hold_s=200e-9, edge_s=1e-9)
assert result['measurements']['passed']
time = result['waveforms']['time']
voltage = result['waveforms']['v(y)']
char = characterize_cell('NANY', destination='cells/out/NANY/NANY.char.json')
curve = dc_transfer(spice, 'NANY', ['A', 'B'], ['Y'], 'A', fixed_trits={'B': 0})
```

`input_vectors(n)` enumerates all input combinations. `transitions=True` makes
an Euler tour of every directed change between distinct **input vectors**; this
includes simultaneous input changes. Its first segment initializes the circuit.
For n=1/2/3 there are 6/72/702 transitions. The default 10000-transition budget
rejects larger tours explicitly. Supply representative vectors for large designs.

`build_testbench` infers the actual `.subckt` pin order. New cells must obey the
project contract; legacy extracted designs may use different pin order. Each
output has a .nodeset guess from the initial ideal result; `nodeset` can add
hierarchical internal-node guesses. These are initial DC guesses, not imposed
transient voltages. A 1e12 ohm shunt aids convergence. Supply voltages are ideal
+5/0/-5 V. Optional `pdk` and `temperature_c` arguments select model directory
and temperature; no model changes or user ngspice startup files are applied.

Checkpoint error is the signed voltage error at segment end minus 1 ns. The
inclusive ±0.5 V band determines level PASS. Settling is measured from **edge
start**, including the 1 ns ramp, to the final band crossing; the output must
stay inside through segment end. Piecewise-linear crossing interpolation has
accuracy limited by the chosen timestep. Null settling means the band was not
reached and maintained. `max_settling_s` excludes the initialization segment;
it is null when there are no transitions. `unsettled` counts failed windows.

Waveform rail currents use the SPICE sign convention (positive into the ideal
voltage source). Per-segment current samples are transient tail estimates;
`dc_operating_points` in `characterize` solves separate true DC operating points.
Input C is a biased, in-circuit 1 MHz AC driving-point measurement, with other
inputs/rails AC grounded and outputs unloaded. It includes Miller response.
Fanout suggestions are nominal heuristics, capped at 4, using the maximum
measured input capacitance and largest tested passing load. They do not qualify
a loaded multi-cell path or PVT corners.

`compare_layout(pre, post, top, inputs, outputs, vectors, expected, **kwargs)`
runs identical stimuli/loads on both netlists and reports post-minus-pre settling
per output and transition. Separate `pre_nodeset`/`post_nodeset` dictionaries are
available if hierarchical names differ. An unsettled delay difference is null.

Characterize extracted library cells from the command line:

```
python3 -m tritflow.sim.characterize INV
python3 -m tritflow.sim.characterize NANY
```

For a source-schematic fallback, explicitly select its source and formal pins:

```
python3 -m tritflow.sim.characterize INV --spice tests/sim/fixtures/inverter.spice --top inverter --inputs vin --output vout --destination /tmp/inverter.char.json
```

Phase 2 characterization includes a cell driving 1/2/4/8 actual copies of itself,
with every receiver input pin tested and the other input held at each trit.
Five-stage chains use a neutral second input (NAND +1, NOR -1, NANY 0) so each
stage propagates all levels. Every driver state and all six scalar transitions
are exercised. The maximum recommendation is the largest tested count passing
all load cases and five-stage restoration; it is a measured bound, not an
extrapolation from input capacitance. `include_cascade=False` selects just the
isolated-cell tests. Their old capacitance estimate remains in the JSON.

```
python3 -m tritflow.sim.cascade --out build/cascade/current
python3 examples/postlayout_all.py
python3 examples/postlayout_all.py --watch --watch-seconds 600
```

The cascade command replays the saved RR20 two-inverter reference read-only,
checks its saved checkpoint values, then tests the actual current RR30 library.
It reuses matching source-hash reports and refuses to publish mixed revisions.
Post-layout validation reads the four GateNetlists/GDS/PNR JSON files, proves
embedded cell geometry matches the current library, snapshots consumed views,
runs strict LVS, adds GDS-derived lumped C, checks independent arithmetic oracles
and writes per-output delay changes, rail IR estimates, waveform npz/ASCII and
standalone Plotly HTML under each `build/<design>/postlayout/`. It rejects inputs
that change during a run. `--rebuild-pnr` invokes the public PNR flow with DRC
when an independent rerun after cell compaction is wanted.

The post-layout plan exhausts all 27 full_add, 81 mac1 and 9 mul1 inputs. Adder4
uses 20 documented cases: setup/trigger/release of both polarities of four-digit
carry propagation, overflow, opposite and alternating operands, and positive/
negative single-digit probes. Input order, labels and independent expected
arithmetic are saved in `vectors.json`. Default hold is 2 us, maximum timestep
2 ns and output load 10 fF; CLI options change timing resolution explicitly.
See `tritflow.viz.waves.waveform_figure` and `transfer_figure` for reusable plots.
