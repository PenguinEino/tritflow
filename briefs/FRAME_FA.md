# FRAME_FA stream brief: the full adder in the stock OSS_FRAME, for Fig. 1

Fig. 1 (`figures/fig_flow_v2.py`) follows `examples/full_add.tv` from HDL to post-layout SPICE. Its new last
panel must show **that same full adder** placed in the stock `OSS_FRAME`, wired like the dot4 top
(`notebook/assets/chip/dot4/`, `docs/status/FRAME.md`): frame ESD VSS = core VSS (−5 V, substrate), frame
ESD VDD a separate +5 V pad, core VDD and VMID on ANA pads.

## Hard constraints
- **Do not edit anything under `tritflow/`, `notebook/*.py`, `notebook/v3/`, `cells/`, `examples/`, `results/`.**
  Recorded campaigns hash those files (`results/dot_scaling.json`, dot4 provenance); any edit breaks chapter 6
  on Colab. Write only under `figures/full_add_chip/` (new: a build script, the GDS, a short JSON/README of
  the pad map and check results) and `docs/status/FRAME_FA.md`. Do not commit.
- The stock path (`tritflow/pnr/chip_frame.py`, `stock_chip`, `_pads`) assumes 8 inputs/2 outputs. Reuse it
  from your script by wrapping or substituting the pad allocation at runtime (e.g. a local function passed in
  or patched on the module object inside your script only) — never by editing the file.
- Macro: the same full adder Fig. 1 already shows: `build/full_add/full_add.gds` and `.json`/`.pnr.json`
  (copied from the main worktree; rebuild with the library flow only if you must, and then say so).

## Task
1. Pad map for 3 inputs (a, b, cin) and 2 outputs (sum, cout) on the 14 ANA pads plus the stock VDD/VSS
   ESD pads. Put core VDD and VMID on as many pads as the current check wants; leave the remaining ANA
   pads in a state the stock template and LVS accept (say what you chose and why). Short, readable routing.
2. Run the same checks the dot4 build runs, with the pinned decks (`TR1UM_PDK=~/pdk/TR-1um-pinned`,
   `NGSPICE_BINARY=~/.local/opt/tritflow-ubuntu-24.04/bin/ngspice`): drawing DRC 0 (stock waivers only),
   strict drawing LVS, and if time allows MDP / mask DRC / MPW precheck (local copy of `~/TR-1um_MPW_Sanken`)
   and the DC current check. Record what ran and what passed. Never report a check you did not run.
3. Output `figures/full_add_chip/tr_1um_full_add.gds` and a summary JSON with die size, pad count and the
   check results, so the figure caption can quote only checks that passed.
4. Time box: stop by **2026-10-29 17:00 JST**. If DRC/LVS cannot be made clean by then, still deliver the
   GDS with an honest summary (the integrator then decides the caption), and record the blocker.

Report in `docs/status/FRAME_FA.md`: pad map, checks run and results, files written, and anything uncertain.
