# Brief: PNR stream — placement, routing, power, GDS for ternary standard cells

You own `tritflow/pnr/`, `tests/pnr/`, `docs/status/PNR.md`. Read `AGENTS.md`, `docs/concept.md`
(section 配置配線), `docs/interfaces.md` first.

## Context
TR-1um has only two metals (M1 13/0, V1 19/0, M2 20/0). Cells use M1 inside and have M1 rails
(top→bottom VDD / body / VMID / VSS). Pins are M1 with access points on vertical grid lines.
The CELLS stream is building the real cells in parallel; until `cells/template.json` and
`cells/out/library.json` exist, develop against `cells/template.provisional.json` and mock cell
abstracts you generate (boxes with pins and M1 obstructions). Switch to the real library
automatically when it appears; keep the mock path for tests.

## Method (decided)
- Floorplan: cell rows alternating with routing channels. Row count chosen for a near-square die;
  channel height adapts to demand.
- Placement: initial placement in signal-flow order (topological level → column), then simulated
  annealing on HPWL with swaps/moves within and between rows, deterministic seed. Record a
  placement history (every k steps) for animation.
- Routing on a grid (pitch = template grid): M2 vertical, allowed over cells except over M2/V1-free
  constraints and obstructions; M1 horizontal only inside channels; V1 at M1/M2 changes and at pin
  access points. Net ordering, A* maze routing, rip-up and reroute; if still failing, widen the
  failing channel and retry. Respect width/spacing (M1 1.8/1.4, M2 3.0/2.0, V1 1.4 with 1.0
  enclosure) and wide-metal spacing rules from the DR table.
- Power: join row rails at both ends with vertical M2 trunks (wide), plus die-level VDD/VMID/VSS
  pins. Size rail/trunk widths from per-cell static current (read `cells/out/<CELL>/<CELL>.char.json`
  when present, else a documented default) and an allowed current density parameter (document it
  as an assumption; the PDK gives no EM number). Respect M1/M2 max width 45 µm (slotting rule) —
  split wide trunks.
- I/O: one M2 pin + TXM2 label per port on the die boundary (inputs left/top, outputs right).
- Output per interfaces.md: `<top>.gds` (cell GDS merged by reference, routing in its own cell),
  `<top>.pnr.json` (placements, wires, vias, pins, power, history).

## Self-checks (before handing to PDK DRC/LVS)
- Geometric connectivity: build nets from the drawn M1/V1/M2 (klayout.db Region / LayoutToNetlist
  or your own union-find) and compare against the GateNetlist: no opens, no shorts.
- Width/spacing check on routing layers (your own, fast).
- Then run the PDK drawing-layer DRC deck on the result (`~/bin/klayout/klayout -b -r ...`).

## CLI / API
- `python3 -m tritflow.pnr build/adder4/adder4.json -o build/adder4/ [--rows K] [--seed S]`.
- `tritflow.pnr.place_and_route(netlist, library, **opts) -> PnrResult` usable from a notebook,
  with `.gds_path`, `.json_path`, `.stats` (die size, wirelength per layer, via count, utilization).

## Tests
Synthetic netlists (chains, fan-out trees, a random 50–200-instance DAG) on mock cells: route 100 %,
connectivity check clean, own DRC clean. When the real library exists, also a small real-cell case
through the PDK DRC deck.

Definition of done: routes the synthetic suite and, once available, a 4-trit adder netlist (FRONTEND
writes `build/adder4/adder4.json`; you may also hand-build one) with clean connectivity and PDK DRC.
