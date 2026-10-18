# Paper figures

Static, print-first figures for the notebook, README, PR and poster. Each script reads the
repository's own data (cells, build outputs, results) and writes PDF, PNG (600 dpi) and SVG to
`figures/out/`. Regenerate all with `PYTHONPATH=. python3 figures/make_all.py` after the final
re-runs; set `FIG_REF=<commit>` to draw `results/` from a committed snapshot.

Style: IEEE column widths, Times-like serif, thin marks, light grid. Trit values use one diverging
encoding everywhere: −1 blue, 0 grey, +1 red. Shaded bands are the ±0.5 V acceptance windows.

| File | Draft caption |
|---|---|
| `fig_flow` | **TritFlow at a glance.** A 4-trit adder written in TritVerilog is synthesized into 44 NANY and 20 INV cells (exhaustive equivalence check), placed and routed on two metals with the three-rail standard cells, checked with the TR-1um DRC deck (0 markers) and LVS (match), and simulated from the extracted layout. |
| `fig_gates` | **Three levels from ordinary CMOS.** DC transfer (a) and supply current (b) of the four logic cells, from their extracted layouts at 27 °C. The middle level is set by a resistive divider, so a gate whose output sits at 0 draws a static current of about 0.4 mA (≈4 mW at ±5 V). |
| `fig_sizing` | **Sizing trades level accuracy against static current.** (a) INV transfer for three resistor lengths at the taped-out W/L. (b) Worst level error vs. static current for 90 INV sizes; open markers fail the ±0.5 V criterion, triangles are below 3 mV. Current is set almost entirely by the resistor length; accuracy by the transistor sizes. (c) The same for the NANY sizes the DC solver resolves. The circled point is the size that was taped out. |
| `fig_cell` | **From a taped-out cell to an abuttable standard cell.** (a) Taped-out NANY. (b) The same circuit and device sizes redrawn as a 132 µm-tall standard cell with VDD, VMID and VSS rails. (c) Four cells abutted; the rails run continuously across the cell boundaries. Same scale in (a) and (b). |
| `fig_synth` | **From TritVerilog to cells.** (a) Source of the half and full adder. (b) The synthesized half adder for a = b = +1, nets coloured by their settled trit. (c) Full adder composed of two half adders, a NANY and an INV (11 NANY + 5 INV), evaluating 1 + 1 + 0 = (−1) + 3·(+1). |
| `fig_pnr` | **Placement and routing of the 4-trit adder.** (a) Initial placement in signal order. (b) After simulated annealing and routing; cells of each full adder (colour) cluster together; Metal 1 runs horizontally in channels, Metal 2 vertically over cells. (c) Half-perimeter wirelength during annealing. |
| `fig_postlayout` | **The layout still works.** (a) The full adder driven through all 27 input combinations (500 ns each, 10 fF loads): extracted devices without and with estimated wire capacitance both settle inside every band. (b) The slowest transition; wiring adds about 10 ns. (c) Worst settling vs. output load; beyond ≈12.8 pF an output no longer settles within the 500 ns window. |
| `fig_scaling` | **One HDL source, six adders.** N-trit ripple adders (N = 1…6) generated, routed, DRC/LVS-checked and simulated. (a) Worst carry/MSB settling grows linearly: ≈49 ns per trit for the extracted devices alone, ≈57 ns per trit with estimated wire capacitance. (b) Idle supply power grows with cell count, ≈4.2 mW per cell, the cost of resistive-divider levels. (c) Die area and cell count. |

Numbers in the captions are from the current data; re-read them after the final regeneration.
