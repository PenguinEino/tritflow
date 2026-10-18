# AGENTS.md

Project: TritFlow — a balanced-ternary Verilog-like HDL → synthesis → P&R → GDS → DRC/LVS →
post-layout ngspice flow on the OpenSUSI TR-1um PDK, delivered as a Colab notebook for the
IEEE SSCS Code-a-Chip ISSCC 2027 call (deadline 2026-10-31 11:59 PT).

Read before working:
1. `docs/concept.md` — decisions (Japanese).
2. `docs/interfaces.md` — the contract between streams, ownership, and ground rules. Binding.
3. Your brief in `briefs/<STREAM>.md`.

Reference material (read-only): `~/balanced-ternary-logic` (taped-out ternary cells, Xschem
schematics, KLayout build scripts under `layout/`, verification scripts under `scripts/`),
`~/pdk/TR-1um` (PDK: PCells under `libs.tech/klayout/tech/python`, DRC/LVS decks under
`libs.tech/klayout/tech/{drc,lvs}`, models under `libs.tech/spice/models`).

Write code that a circuit-design expert can read: small modules, docstrings that explain the
circuit meaning, no dead code. Status notes in `docs/status/` may be English or Japanese.
