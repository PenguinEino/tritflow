# Brief: STA stream — static timing analysis for ternary logic

You own `tritflow/sta/`, `tests/sta/`, `results/sta/`, `docs/status/STA.md`.
Read `AGENTS.md`, `docs/interfaces.md`, and the status files of CELLS, SIM and PNR first.

## Why
Binary STA measures delay at one 50 % threshold. A ternary output has three levels, six directed
transitions, and "settled" means entering and staying in the ±0.5 V band of the new level. The
notebook wants a fast analytical timing estimate that a designer can trust, checked against
post-layout SPICE.

## Deliverables
1. Timing model per cell from characterization data (`cells/out/<CELL>/<CELL>.char.json`, and the
   timing tables CELLS is adding — see docs/status/CELLS.md): settling time as a function of load
   (and input transition if available) for each directed input→output transition class
   (−1→0, 0→+1, −1→+1, …). Interpolate; document extrapolation limits.
2. Graph-based STA over a GateNetlist with per-net load = fan-out input capacitance + wire C
   (from `tritflow.extract` wire-capacitance estimate on the P&R result when available, else
   fan-out only): worst-case arrival per output, the critical path listed cell by cell with the
   transition class at each stage, and which input vector pattern sensitizes it (ternary-aware: a
   path through NANY/NAND/NOR only propagates certain transitions — handle this with per-transition
   arrival times, not a single delay per arc; explain the approach in docstrings).
3. Validation against SIM's post-layout results (`results/adder_scaling.json`, the four example
   designs under build/*/postlayout/): predicted vs simulated worst settling for each output;
   report error statistics in `results/sta/validation.json` and a figure function
   (`tritflow/sta/plot.py`, Plotly) for notebook chapter 7.
4. Public API: `tritflow.sta.analyze(netlist, pnr=None) -> TimingReport` with `.critical_path`,
   `.arrival`, `.to_html()`.

Definition of done: tests pass, validation on adders N=1..6 and the four examples recorded with
honest error bounds, status updated.
