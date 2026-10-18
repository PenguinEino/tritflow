# TritFlow interfaces (shared contract between work streams)

Owner: integrator (Claude). Streams must not change this file; propose changes in
`docs/status/<stream>.md` under "Interface requests".

All lengths are µm, origin at the lower-left corner of the cell/die prBoundary.
Electrical: VDD=+5 V, VMID=0 V, VSS=−5 V. Trit −1/0/+1 ↔ −5/0/+5 V. A node passes a
check when |V − ideal| ≤ 0.5 V. PDK: `$TR1UM_PDK` (default `~/pdk/TR-1um`).
Constants live in `tritflow/__init__.py`.

## Repository layout and ownership

| Path | Owner stream |
|---|---|
| `tritflow/__init__.py`, `tritflow/netlist.py`, `docs/interfaces.md`, `pyproject.toml`, `AGENTS.md` | integrator |
| `tritflow/cells/`, `cells/`, `tests/cells/` | CELLS |
| `tritflow/hdl/`, `tritflow/synth/`, `examples/`, `tests/hdl/`, `tests/synth/` | FRONTEND |
| `tritflow/pnr/`, `tests/pnr/` | PNR |
| `tritflow/sim/`, `tritflow/extract/`, `tests/sim/`, `tests/extract/` | SIM |
| `tritflow/viz/graph.py`, `tests/viz/` | FRONTEND |
| `tritflow/viz/waves.py`, `tritflow/viz/scaling.py`, `results/`, `cells/out/sizing/` | SIM |
| `tritflow/viz/cell.py`, `tests/viz/test_cell*.py` | CELLS |
| `tritflow/viz/layout.py`, `tests/viz/test_layout*.py`, `examples/fuzz_pnr.py`, `examples/pnr_all.py` | PNR |
| `tritflow/flow.py` | FRONTEND |
| `notebook/` | FRONTEND (draft) |
| other `tritflow/viz/` | later |
| `tritflow/sta/`, `tests/sta/`, `results/sta/` | STA |
| `docs/status/<stream>.md` | that stream |

## Cell library

| Cell | Pins (signal, in order) | Function (trits) | Uses VMID |
|---|---|---|---|
| INV | A → Y | Y = −A | no (rail passes through) |
| NAND | A, B → Y | Y = −min(A,B) | no |
| NOR | A, B → Y | Y = −max(A,B) | no |
| NANY | A, B → Y | Y = −clamp(A+B, −1, 1) | yes |
| BUF | A → Y | Y = A (INV+INV) | no |
| TIEP / TIEZ / TIEN | Y | +1 / 0 / −1 | TIEZ only |
| FILL | — | — | — |

Power pins VDD, VMID, VSS exist on every cell. SPICE subckt port order:
signal pins in table order, then `VDD VMID VSS`. Subckt names are the cell names.

Rails, top to bottom: VDD / cell body / VMID / VSS (all horizontal M1, abutting).
Cell interior: M1 and poly preferred; M2/V1 are allowed where they keep the cell compact, and every
internal M2/V1 shape must appear in the abstract's `obstructions` (the router treats them as blocked).
Target: cell area within ~2x of the taped-out layouts. Allowed orientations: R0, MY.

### `cells/template.json` (CELLS owns; `cells/template.provisional.json` is a placeholder)

```json
{
  "height": 0, "grid": 6.0,
  "rails": {"VDD": [y0, y1], "VMID": [y0, y1], "VSS": [y0, y1]},
  "pin_rows": [y, ...],
  "layers": {"M1": [13,0], "V1": [19,0], "M2": [20,0], "TXM1": [48,0], "TXM2": [49,0],
             "pin": [48,1], "prBoundary": [235,0]},
  "rules": {"M1_w": 1.8, "M1_s": 1.4, "M2_w": 3.0, "M2_s": 2.0, "V1": 1.4, "V1_enc_M1": 1.0, "V1_enc_M2": 1.0}
}
```
Cell width is a multiple of `grid`. Pin access points lie on vertical grid lines
(x = k·grid + grid/2) so a V1 dropped from an M2 track lands on the pin.

### `cells/out/<CELL>/` (CELLS)

- `<CELL>.gds` — top cell named `<CELL>`, with prBoundary and pin labels.
- `<CELL>.spice` — schematic-level subckt (devices + PDK model names).
- `<CELL>.ext.spice` — LVS-extracted subckt.
- `<CELL>.abstract.json`:
```json
{"name": "NANY", "width": 0, "height": 0,
 "pins": {"A": {"dir": "input", "layer": "M1", "rects": [[x0,y0,x1,y1]], "access": [[x,y]]},
          "Y": {"dir": "output", ...}},
 "obstructions": {"M1": [[x0,y0,x1,y1]], "M2": []}}
```
- `<CELL>.char.json` — characterization (SIM fills; schema in SIM status file).
- `cells/out/library.json` — list of cells with paths; `cells/out/all.spice` includes every subckt.

## Gate netlist (`tritflow.netlist.GateNetlist`, FRONTEND → PNR, SIM)

```json
{"top": "adder4",
 "ports": [{"name": "a[0]", "dir": "input"}],
 "instances": [{"name": "g1", "cell": "NANY", "pins": {"A": "a[0]", "B": "b[0]", "Y": "n1"},
                "hier": "fa[0].u.ha1"}]}
```
Every net has exactly one driver (a cell output or an input port). Port names are bit-blasted.

## P&R result (PNR → SIM, viz)

- `<out>/<top>.gds` — top cell `<top>`: cell instances by reference (cell GDS merged in),
  plus routing; M2 pins + TXM2 labels on the die boundary for every port; rail labels.
- `<out>/<top>.pnr.json`:
```json
{"die": [w, h], "rows": [{"y": 0, "orient": "R0"}],
 "placements": [{"inst": "g1", "cell": "NANY", "x": 0, "y": 0, "orient": "R0"}],
 "wires": [{"net": "n1", "layer": "M1", "width": 1.8, "points": [[x,y],[x,y]]}],
 "vias": [{"net": "n1", "x": 0, "y": 0}],
 "pins": [{"name": "a[0]", "layer": "M2", "rect": [x0,y0,x1,y1]}],
 "power": {"straps": [...]},
 "history": [{"step": 0, "hpwl": 0, "placements": [...]}]}
```

## Simulation / extraction (SIM)

- `tritflow.sim` runs ngspice in batch mode with the PDK models, returns numpy waveforms,
  and provides measurements: level error vs ideal trit, settling time into the ±0.5 V band
  (the ternary replacement for a 50 % delay), static supply current per input vector.
- `tritflow.extract` turns a GDS into a SPICE netlist with the PDK KLayout LVS deck, adds
  per-net lumped wire capacitance from geometry, and runs LVS against a GateNetlist.

## Ground rules for every stream

- Work only inside your owned paths. Read anything else; never edit it.
- Do not run `git commit`, `git checkout`, `git reset`, `git stash` or anything that changes
  git state. The integrator commits.
- Never modify `~/pdk/TR-1um` or `~/balanced-ternary-logic`; copy what you need.
- Python 3.12 system interpreter; `klayout.db` 0.30.6, KLayout binary at `~/bin/klayout/klayout`,
  ngspice 46. Install extra Python packages only with
  `python3 -m pip install --user --break-system-packages <pkg>` and list them in your status file.
- Keep `docs/status/<stream>.md` current: done, in progress, blockers, interface requests,
  how to run your tests.
- Tests: `python3 -m pytest tests/<your area>` must pass before you report done.
