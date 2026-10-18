# Brief: SIM stream — ngspice harness, characterization, extraction, LVS, IR drop

You own `tritflow/sim/`, `tritflow/extract/`, `tests/sim/`, `tests/extract/`, `docs/status/SIM.md`.
Read `AGENTS.md`, `docs/concept.md` (sections 抽出とSPICE, 特性評価), `docs/interfaces.md` first.
Study how `~/balanced-ternary-logic/scripts/*.py` drive ngspice, include the PDK models
(`$::LIB/ip62_models` → find the real path under `~/pdk/TR-1um/libs.tech/spice/models`), and run
extraction; reuse ideas, copy code you need, never import from that repo.

## 1. Simulation harness (`tritflow.sim`)
- Batch ngspice runner (temp dir, deterministic, timeout, clear errors), raw/ASCII output → numpy.
- Testbench generator for any subckt: ideal VDD/VMID/VSS sources, input vector sequences
  (hold time per segment, 1 ns edges, configurable), per-output load capacitors, `.nodeset` help
  for the initial point, optional exhaustive vector ordering that covers every directed transition
  between input values where feasible.
- Measurements: level error vs ideal trit at check points (1 ns before segment end), PASS/FAIL with
  the ±0.5 V band, settling time = time from input edge until the output enters and stays in the
  ±0.5 V band of its new ideal value (the ternary replacement for 50 % delay), static supply current
  per input vector from each rail, DC sweep helpers (transfer curves).
- Notebook-friendly API returning plain dicts/arrays.

## 2. Cell characterization (`tritflow.sim.characterize`)
For each logic cell: DC output error for all input combinations, static current per combination,
input capacitance (method documented), settling time vs load (10 fF, 100 fF, 1 pF) for every
directed transition, a max-fanout suggestion. Writes `cells/out/<CELL>/<CELL>.char.json` — this is
the one file you may write under `cells/out/`; define its schema in your status file. Until CELLS
delivers `cells/out/*/<CELL>.ext.spice`, develop against netlists you build from the source
schematics in `~/balanced-ternary-logic` (e.g. `xschem -n -s -q -x` netlisting into your own temp
dir, or the existing `*.extracted` files).

## 3. Extraction and LVS (`tritflow.extract`)
- Run the PDK KLayout LVS deck (`~/pdk/TR-1um/libs.tech/klayout/tech/lvs`, batch
  `~/bin/klayout/klayout -b -r ...`) on a GDS: extracted SPICE netlist and LVS against a reference
  SPICE netlist (built from a GateNetlist + cell subckts). Report match / mismatches readably.
- Wire capacitance: per-net lumped C from M1/M2 geometry (area + fringe per perimeter, to substrate).
  Find coefficients in the PDK (model files, docs); if absent, use documented textbook values for a
  1 µm process and label them as assumptions. Append as capacitors to the extracted netlist.
- IR drop: from a `<top>.pnr.json` power description + sheet resistances (find in PDK, else
  assumption) + per-cell static currents (char.json), solve the rail resistive network; report
  per-cell rail voltages and the resulting shift of the ternary 0 level (resistive-divider cells
  INV/NAND/NOR set 0 from VDD/VSS). Treat this as an estimate.
- Integration test now: extract `~/balanced-ternary-logic/full_adder.gds` (copy it), compare with
  `full_adder.extracted`, and simulate its 27 input combinations post-layout — all PASS.

## 4. Pre- vs post-layout comparison helper
Given a GateNetlist SPICE and an extracted netlist of the same design, run the same vectors and
report per-output settling difference. This feeds notebook chapter 7.

Definition of done: harness + measurements tested; characterization runs on at least INV and NANY
(source-schematic netlists until real cells exist); full_adder extraction + LVS + 27-vector post-layout
PASS; IR-drop solver tested on a synthetic rail; status updated with schemas and how to run.

## Phase 2 (added by integrator)
Characterization must include cascade behaviour (a cell driving N copies of itself and chains of
5 cells), reusing the original chain tests in `~/balanced-ternary-logic/simulation/cascade` as the
reference, so the max-fanout suggestion rests on measured data.
