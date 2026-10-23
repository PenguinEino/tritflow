# SCALE stream brief: recorded scaling results for chapter 6

Work in `~/code-a-chip-v3`, only on: `examples/dot_scaling.py` (new), `results/dot_scaling.json` (+ any
companion files under `results/dot_scaling/`), `notebook/scale_views.py` (new), `tests/` for these, and
`docs/status/SCALE.md`. Do not edit `notebook/views.py`, `notebook/v3/*`, narrative files. Do not commit.
Read `AGENTS.md`, `docs/notebook-v3/STORYBOARD.md`, `briefs/V3.md` (context), `notebook/cache.py`,
`results/adder_scaling.json` and the code that made it (`examples/adder_scaling.py`) for the recording
and provenance conventions.

Produce the data and views chapter 6 uses to evaluate the ternary-weight dot product
y = Σ wᵢ·xᵢ (1-trit w and x, written with `*` and `+` in TritVerilog) at N = 2, 4, 8, 16 terms
(and 32 if P&R and SPICE stay tractable; say so either way). For each N, with seed 0:
- synthesis: cells by type, equivalence result (exhaustive or the 100k random mode);
- P&R: die size, rows, estimated and routed wire length, vias, P&R runtime; DRC (violations) and LVS (match)
  with the PDK decks;
- timing: ternary STA worst arrival per output under a fixed, documented set of vector pairs
  (weights fixed, activations changing so the adder tree's longest carry path is exercised);
- post-layout SPICE with extracted wire capacitance, same vectors, ngspice-42
  (`NGSPICE_BINARY=~/.local/opt/tritflow-ubuntu-24.04/bin/ngspice`), PDK `~/pdk/TR-1um-pinned`:
  pass/fail against the ±0.5 V band and slowest settling per output; STA vs SPICE error;
  if SPICE is too slow for the largest N, record it as not simulated and why;
- static supply current and power from ±5 V per input state: all-zero activations (worst case, every
  resistive divider conducts), and the measured spread over the simulated vectors; report per cell.
Record with source/PDK/simulator hashes like the existing campaigns, so the notebook can show recorded
results and recompute behind an explicit switch. Then write small view functions in
`notebook/scale_views.py` in the house style (`notebook/style.py`, booktabs tables, paper-style Plotly as
in `views.py`), Japanese labels, e.g. `scaling_table(data)`, `scaling_figure(data)` (area and delay vs N,
STA vs SPICE), `power_table(data)`. Render them to PNG with headless Chrome and look at them.
Report the numbers and anything surprising (e.g. delay or power growth) in the status file; V3 writes
the chapter text from it.

## Additions from the juror-eye review (integrator, 2026-10-23)

- Layout penalty: per N, ternary STA with and without the extracted wire capacitance (cheap); and, for
  N = 4 only, post-layout SPICE with device-only netlist vs with wire C.
- Power: state the sign convention; report static power at all-zero activations (sum over VDD and VSS
  sources), the average supply power over the simulated vectors and hold time, and separate switching
  energy per transition only if it is cleanly measurable; otherwise say it is not separated.
