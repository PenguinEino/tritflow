# Brief: CELLS stream — ternary standard-cell library for TR-1um

You own `tritflow/cells/`, `cells/`, `tests/cells/`, `docs/status/CELLS.md`.
Read `AGENTS.md`, `docs/concept.md` (section スタンダードセル), `docs/interfaces.md` first.

## Goal
A standard-cell library (INV, NAND, NOR, NANY, BUF, TIEP, TIEZ, TIEN, FILL) that a placer can
abut in rows and a router can reach from M2, every cell DRC- and LVS-clean with the PDK decks.

## Circuits and sizes (reuse the taped-out designs in `~/balanced-ternary-logic`)
- INV: `inverter.sch` MOS W/L; resistors RR W=2.8 µm, L=30 µm.
- NAND, NOR: `mul_nand.sch`, `mul_nor.sch` MOS W/L; RR L=30 µm (the 2026-09-24 MAC improvement
  moved all RR to 30 µm — check `MAC_IMPROVEMENTS.md` and the current .sch values).
- NANY: current `nany.sch` (RR 30 µm). Only NANY uses VMID.
- BUF = INV→INV in one cell. TIEP/TIEZ/TIEN connect Y to VDD/VMID/VSS (choose a safe structure,
  document why). FILL: rails + well continuity only.
- Resistor substrate / MOS body connections exactly as in the source schematics.
- Build devices only from the PDK PCells, as `~/balanced-ternary-logic/layout/build_*.py` do
  (copy the helpers you need; do not import from that repo).

## Template rules (binding unless DRC forces a change — then document it)
- Common height, width = multiple of `grid`. Rails top→bottom VDD / body / VMID / VSS, horizontal M1,
  full cell width, so abutted cells form continuous rails. VMID sits between the body and VSS.
- Interior: M1 + poly only. No V1, no M2 anywhere in a cell.
- Signal pins on M1 with an access point on a vertical grid line x = k·grid + grid/2, sized so a
  V1 (1.4 µm, 1.0 µm M1 and M2 enclosure) dropped from an M2 track lands cleanly.
- Well and substrate contacts inside each cell, continuous when abutted (no tap cells).
- prBoundary (235/0) drawn; abutting any two cells (R0 and MY) must be DRC-clean.
- Pick `height`, `grid`, rail widths and pin rows from the DRC table
  (`~/pdk/TR-1um/Document/TR-1um_Drawing_Layer_DR_Table.csv`) and the largest cell (NANY).
  Rails carry DC current (ternary cells draw static current); make them as wide as is reasonable
  and record the reasoning. Grid ≥ 6.0 µm is expected (M2 3.0/2.0 plus via pads).

## Deliverables
1. `cells/template.json` (schema in interfaces.md), with a short rationale in the status file.
2. Generator: `python3 -m tritflow.cells build` → `cells/out/<CELL>/` files listed in
   interfaces.md, plus `cells/out/library.json` and `cells/out/all.spice`.
3. Verification: `python3 -m tritflow.cells verify` runs the PDK KLayout DRC deck on every cell
   and on an abutment test row (all cells side by side in R0 and MY), and the PDK LVS deck for every
   cell against `<CELL>.spice`; writes `cells/out/verify_report.json`. Figure out how the decks are
   invoked (`~/pdk/TR-1um/libs.tech/klayout/tech/{drc,lvs}`, batch mode `~/bin/klayout/klayout -b -r`);
   use the drawing-layer DRC deck. Anything the deck flags that the original taped-out cells also
   flag must be explained, not ignored.
4. Quick DC sanity sim of each logic cell's 9 (or 3) input points from `<CELL>.ext.spice` with
   ngspice and the PDK models, all outputs within ±0.5 V of ideal. (The SIM stream does full
   characterization later; keep yours minimal.)
5. Abstract PNG renders of each cell (KLayout layout view to PNG) in `cells/out/<CELL>/`.

Order: template + INV + NANY end to end first (DRC/LVS clean), then the rest.
Definition of done: all cells DRC/LVS clean, abutment row DRC clean, tests pass, status updated.

## Phase 2 (added by integrator): prove the new cells are the taped-out cells
The circuits come from a design that passed simulation, chain tests, DRC/LVS and tape-out. The
re-drawn layouts must be shown to behave the same, using the original verification as the bar:
- Re-run the original checks on the new extracted cells: the `scripts/check_<cell>_extracted.py`
  style tests (2-D DC grid, all directed transitions such as NANY's 72) and the chain/cascade tests
  (`simulation/cascade`, inverter_chain, nor_chain). Port them into `tests/cells/` / `tritflow/cells/`.
- Netlist equivalence: same devices, sizes and connectivity as the source schematic (LVS against the
  schematic netlist, not only against your own spice).
- Side-by-side table, original extracted cell vs new extracted cell: DC level errors, static current,
  worst settling time at 10 fF, chain behaviour. Differences must be explained (layout parasitics).
- Write `cells/out/equivalence_report.json` and a readable section in `docs/status/CELLS.md`.

## Phase 3 (added by integrator): compact the cells — this overrides the no-M2 rule above
Phase-1 cells are 462 µm tall; INV is 360×462 µm vs the taped-out 96×66 µm, NANY 678×462 vs 148×115.
That is 18–26× the area and adds long poly buses the taped-out cells never had, which hurts both
speed and the claim that these are the taped-out cells.
- New rule (see updated docs/interfaces.md): M2/V1 may be used inside a cell when it keeps the cell
  compact; every internal M2/V1 shape goes into the abstract's `obstructions`. Leave at least a few
  M2 tracks per cell free for over-cell routing where you can, and say how many in the abstract.
- Start from the taped-out layouts' device placement and internal wiring
  (`~/balanced-ternary-logic/layout/build_*.py`) and adapt them to the common height and rails,
  rather than redrawing from scratch. Target: area within ~2× of the originals, common height as
  low as NANY allows (expect roughly 120–180 µm).
- Re-run phase 1 and phase 2 checks on the compact cells; keep the 462 µm version only if the
  compact version cannot be made DRC/LVS clean (then explain why).
