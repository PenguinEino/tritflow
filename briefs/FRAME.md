# FRAME stream brief: put the dot4 top in the stock OSS_FRAME, wired like the taped-out chip

Work in `~/code-a-chip-v3`, only on: `tritflow/pnr/chip*.py` and `tritflow/pnr/signoff.py` (as needed),
`notebook/assets/chip/dot4/`, `notebook/reuse.py` (pad table / view only), `tests/` for these, and
`docs/status/FRAME.md`. Do not edit `notebook/views.py`, `notebook/style.py`, `notebook/v3/*` or the
narrative files; the integrator updates the text. Do not commit. Read `AGENTS.md`, `docs/status/SHUTTLE.md`,
`notebook/assets/chip/dot4/README.md` and `tritflow/pnr/chip.py` first.

## Why
The current dot4 top copies `OSS_FRAME_TEG` and replaces its pad bank with ESD-less `OSS_PAD_TEG`
probe pads. The author's taped-out ternary chip did not do that: it sits in the stock `OSS_FRAME`
(14 × `OSS_ESD_5V_ANA` signal pads + `OSS_ESD_5V_VDD` + `OSS_ESD_5V_VSS`) of
`~/ISHI-KAI_Multiple_Projects_OpenMPW_OpenSUSI-TR10-1_AUDIO_OPAMP07` (`src/tr_1um_AUDIO_OPAMP07.gds`,
pin list in `docs/pin_list.pdf`). There the ternary VDD (+5 V) and VMID (0 V) enter through ordinary
ANA pads; the ternary VSS (−5 V) is the frame's common ESD VSS, which is also the substrate; the
frame's ESD VDD is a separate pad. With ESD VSS = −5 V and ESD VDD held at +5 V, every pad swings
inside the ESD rails, so −5/0/+5 V signals pass the ANA pads with their clamps off. Use the same method.

## Task
1. Build the dot4 MPW top (the same programmable 46-cell dot4 macro, seed 0, as now) inside the
   unmodified stock `OSS_FRAME` from the pinned PDK (`$TR1UM_PDK/libs.tech/klayout/libraries/TR-1um_frame_25x25.gds`),
   centered 2500 × 2500 µm, exactly as the organizer's template expects (compare with
   `~/TR-1um_MPW_Sanken/src/tr_1um_sanken.{gds,cir}` and the AUDIO_OPAMP07 top for how the frame,
   its pads and its nets appear in the GDS and in the LVS netlist).
2. Pad assignment: frame ESD VSS pad and ring = VSS (−5 V, substrate); frame ESD VDD pad = ESD VDD,
   a separate terminal that must be held at +5 V (do not tie it to the core VDD inside the chip unless
   the current check below requires it — then say so); on the 14 ANA pads: 8 inputs, 2 outputs, VMID,
   and core VDD on as many of the remaining pads as the current check needs. Choose an order that keeps
   the routing short and readable; record the map.
3. Checks, all with the pinned decks and native reports as now: drawing DRC 0 (no waivers), strict
   drawing LVS match (the frame's ESD devices included as the template does), MDP, mask DRC 0, the
   organizer's precheck on a local copy of `~/TR-1um_MPW_Sanken`, and the existing DC current check
   on every supply path (pad, ring and via) with at least 20 % reserve. If one ANA pad per supply is
   not enough, use more pads; if the frame VSS ring cannot carry the VSS current, say so with numbers.
4. Replace the published snapshot under `notebook/assets/chip/dot4/` (GDS, .cir, mask GDS, pad map,
   signoff, provenance, evidence, KLayout PNG with legend, README). The README states the operating
   condition: ESD VDD at +5 V, applied before or together with core VDD; ESD VSS = core VSS = −5 V.
   Keep `submission_ready` honest: list only what still needs the organizer (allocation of a full
   2500 µm slot, bond diagram, final CI), and drop items the stock frame now covers.
5. Keep `shuttle_view()` working with the new pad table; update tests (hash checks, pad count, frame
   cell name). If the TEG path is no longer used by anything, remove it rather than leaving dead code;
   if `tests/pnr/test_chip.py` or other callers still need it, keep it and say why.
6. Render the KLayout PNG and the `shuttle_view()` output with headless Chrome and look at them: the
   pad ring must be visible and every pad's net readable in the table.

Run locally with `TR1UM_PDK=~/pdk/TR-1um-pinned` and `NGSPICE_BINARY=~/.local/opt/tritflow-ubuntu-24.04/bin/ngspice`.
Report in `docs/status/FRAME.md`: pad map, check results, current reserve per supply, what changed in
code, and anything the integrator must change in the chapter 6 text. If the stock frame cannot be made
clean by 2026-10-24 18:00 JST, stop, record why, and leave the current snapshot untouched.
