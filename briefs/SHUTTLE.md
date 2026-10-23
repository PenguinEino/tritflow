# SHUTTLE stream brief: reuse cell and shuttle-ready top for chapter 6

Work in `~/code-a-chip-v3`, only on: `notebook/reuse.py` (new), `notebook/assets/chip/dot4/` (new),
`tritflow/` additions needed for a one-call flow if any (keep them small, documented, tested),
`tests/` for these, and `docs/status/SHUTTLE.md`. Do not edit `notebook/views.py`, `notebook/v3/*`,
narrative files. Do not commit. Read `AGENTS.md`, `docs/notebook-v3/STORYBOARD.md`, `briefs/V3.md`
(context), the v1 notebook's chapter 8 and 9 code (`notebook/methods.py`, `notebook/stages.py`,
`notebook/assets/chip/adder4`, `tritflow/pnr/chip*`).

1. Reuse: a function the chapter-6 cell calls on any TritVerilog source string that runs the whole flow
   with the existing step logs (`notebook/live.py` step/need): synthesize → place and route (live view,
   replay) → DRC → LVS → extract → post-layout SPICE with a reasonable automatic stimulus (every input
   pattern if small, otherwise a documented sample) → result summary; errors in the HDL show the
   existing error box, not a traceback wall. One editable HDL cell + one call is the whole reader action.
   Default source: dot4 with the weights fixed as constants (e.g. `assign y = x0 - x1 + x2 + x3;`
   derived from w = (+1, −1, +1, +1)) so the reader sees constant weights folded away; check the cell
   count drops and say how much.
2. Shuttle: the MPW-frame top for dot4 (pads, frame, rails) with the existing tooling, DRC/LVS clean with
   the PDK decks, saved under `notebook/assets/chip/dot4/` with provenance, plus a view (GDS viewer and
   a pin/pad table). If the tooling cannot produce it cleanly by the evening of 2026-10-24 JST, stop,
   record why in the status file, and leave the adder4 snapshot as is.
Execute everything locally with ngspice-42 (`NGSPICE_BINARY=~/.local/opt/tritflow-ubuntu-24.04/bin/ngspice`)
and `TR1UM_PDK=~/pdk/TR-1um-pinned`; render outputs to PNG with headless Chrome and look at them.
