# FRAME status

## Scope and decisions — 2026-10-23

- Read the project instructions, concept, binding interfaces, FRAME brief,
  SHUTTLE status, existing dot4 snapshot and chip implementation.
- Work is limited to `tritflow/pnr/chip*.py`, `tritflow/pnr/signoff.py` if
  required, `notebook/assets/chip/dot4/`, the pad/view part of
  `notebook/reuse.py`, relevant tests, and this status file. No commit/push.
- Use the pinned PDK and the specified local ngspice binary. Preserve the
  programmable 46-cell dot4 macro (seed 0, 600 annealing steps).
- Build and qualify in the snapshot's ignored `.work/` directory. The binding
  integrator decision below accepts the organizer's unchanged stock frame
  exceptions while requiring zero native DRC items and no exceptions of our own.
- Target the unmodified stock `OSS_FRAME`: common ESD VSS/substrate is core
  VSS (−5 V), separate ESD VDD is +5 V, and core VDD/VMID use ANA pads.

## In progress

None. FRAME is complete under the binding stock-frame policy.

## Done

- Canonical stock-frame snapshot published locally: GDS, mask GDS, independent
  ESD-inclusive `.cir`, 16-pad map, signoff/provenance, native evidence archive,
  KLayout raster/legend and headless-Chrome images. No commit or push.
- The existing `shuttle_view()` opens the canonical stock chip with all 16 pad
  nets readable. `notebook/reuse.py` needed no change. Inspected the direct
  KLayout PNG and both Chrome screenshots; the complete pad ring is visible.
- Removed the rejected-candidate script/package and earlier candidate scratch
  builds. The separate adder4 snapshot is untouched.

## Stock-frame policy — binding integrator decision, 2026-10-23

- The pinned `OSS_FRAME` has **two stock 63/0 DRC waiver polygons**, in
  `OSS_LOGO_TR` and `OSS_FRAME_CNR0`. Their union is **63400 µm²**. The
  unmodified decks identify 63/0 as the DRC waiver layer.
- The integrator explicitly overrode the brief's blanket “no waivers” wording:
  preserve those organizer-owned markers, accept zero-item native reports
  with stock waivers honored, and reject any 63/0 geometry of our own.
- The ownership audit skips only the actual identity-placed `OSS_FRAME`
  instance. It counts every 63/0 shape elsewhere, including a duplicate placed
  inside a stock waiver's area. **Own polygon count and area are both zero.**
- Native drawing and mask reports each have **zero items**, without filtering
  warnings or accepting any report item in our macro/routing/pad/power geometry.
- Native MDP changes **0.001508 µm² of M2** in the stock logo, identically
  for the isolated frame and full chip. CO/M1/V1 XOR areas are zero.
- The same binding decision accepts that organizer-owned logo change. An
  independent stock-frame-only MDP run provides the exact delta region.
  Full-chip XOR minus that region is **exactly zero**, and overlap of any
  delta with our hierarchy's conductor geometry is **exactly zero**.
  The full-die 0.001508 µm² remains visible in the report; it is not rounded away.
- `clean=true` and `physical_checks_passed=true` on that basis. Native zero-item
  DRC, strict ESD-inclusive LVS, exact frame integrity, MPW precheck and DC
  reserve all pass. `submission_ready=false` remains intentional for the full
  slot, final bond diagram and organizer metadata/CI only.

## Blockers

None after the binding integrator decision.

## Canonical stock-frame pad map

| Pad | Stock pin | Net | Center (µm) |
|---|---|---|---|
| P01 | P1 | VDD | −200, 1040 |
| P02 | P2 | VDD | −600, 1040 |
| P03 | P3 | x1 | −1040, 600 |
| P04 | P4 | x0 | −1040, 200 |
| P05 | P5 | w3 | −1040, −200 |
| P06 | P6 | w2 | −1040, −600 |
| P07 | P7 | w0 | −600, −1040 |
| P08 | VSS | VSS | −200, −1040 |
| P09 | P9 | x3 | 200, −1040 |
| P10 | P10 | w1 | 600, −1040 |
| P11 | P11 | y[1] | 1040, −600 |
| P12 | P12 | y[0] | 1040, −200 |
| P13 | P13 | VMID | 1040, 200 |
| P14 | P14 | x2 | 1040, 600 |
| P15 | P15 | VDD | 600, 1040 |
| P16 | VDD | ESD_VDD | 200, 1040 |

P08 is `OSS_ESD_5V_VSS`; P16 is `OSS_ESD_5V_VDD`; the other 14 are
`OSS_ESD_5V_ANA`. All three core VDD pads join on-chip. ESD VDD is separate
and must be +5 V before or together with core VDD. ESD VSS, core VSS and
substrate are −5 V. VMID is 0 V. The AUDIO_OPAMP07 pin list/GDS and the
Sanken `.cir`/GDS were inspected read-only to establish this topology.

## Electrical and physical results

- Exact original seed-0 macro GDS, not just equal logic/cell count: **46 cells,
  1692 × 1206 µm**, centered in **2500 × 2500 µm**. 600 annealing steps.
- Strict drawing LVS **matches**, including `OSS_FRAME` and all three ESD pad
  types. No port restoration was needed. Full drawn-metal connectivity and
  every layer/text of the imported stock frame match their references.
- The actual organizer precheck passes in a local copy of the Sanken template.
- Conservative per-rail core current envelopes are VDD **19.36159 mA**,
  VSS **19.36159 mA**, VMID **0.210094 nA**. Three 40 µm M1 VDD feeders and
  six banks of four 9.4 µm M1 VSS fingers meet the existing DC solver's target.
  Real 14 µm ring lanes, periodic bridges, pad fingers and small TC arrays
  are included; all modeled conductors/cuts are checked against actual GDS.
- With a **1 µA auxiliary leakage budget on every supply path**, minimum
  reserves are VDD **31.1755%**, VSS **25.1964%**, VMID **99.8718%** and
  ESD_VDD **99.7778%**. The VSS ring's worst 14 µm M2 branch is bounded at
  **6.65418 mA / 17.26667 mA**, giving **61.4623% reserve**. The ring passes.
- Native pinned ESD MPE/MNE models at 27 °C, all three pad levels: maximum
  summed absolute current **0.542608 nA**, including 14 ANA and both rail
  clamps. The 1 µA budget covers that result conservatively.
- A stock pad's continuous 70 µm TC receives the entire rail-current upper
  bound. Its limit uses 780 µA × (70 / 1.4), a conservative minimum-width
  engineering scaling, explicitly not a published pad/lifetime EM rating.

## Interface requests / chapter 6

- The canonical snapshot now uses the stock 16-pad `OSS_FRAME`, not a custom
  17-pad TEG bank. Explain the separate +5 V ESD VDD terminal, applied before
  or together with core VDD, and common −5 V ESD/core VSS/substrate.
- All three core VDD ANA pads must be powered. The frame VSS ring passes the
  current check; it is not a limiting blocker. Core VDD is not tied on-chip
  to ESD VDD. VMID uses one ANA pad at 0 V.
- State the two organizer-owned stock waiver polygons and frame-only MDP
  delta explicitly. There are no TritFlow waiver shapes or metal changes.
- Drop custom pad-bank/missing-ESD approval language. Remaining organizer work:
  a full 2500 µm slot, final bond diagram, and final submission metadata/CI.
- The legacy TEG implementation is retained because `tests/pnr/test_chip.py`
  exercises full-adder wrapping and the separate adder4 snapshot still uses
  it. `frame="OSS_FRAME"` selects the stock allocation, with failure preserving
  all previous canonical GDS/reference/metadata bytes.
- No unowned narrative/view/style/v3 files were edited. No packages installed.

## Code changes and reproduction

- `chip.py`: explicit stock-frame selection, native ESD LVS, separate frame-only
  MDP, stock-policy audit, source/evidence cache fingerprints and actual precheck
  in a copied Sanken template. TEG default callers remain compatible.
- `chip_power.py`: reuse the existing macro distribution header without creating
  legacy TEG supply pads when building the stock wrapper.
- `chip_frame.py`: exact stock hierarchy, selected pad map, centered macro,
  routing, independent schematic reference, and fail-closed publication.
- `chip_frame_power.py`: three VDD feeders, six VSS finger banks, actual slotted
  ring/pad model, per-supply reserve, and pinned ESD-model DC leakage check.
- `chip_frame_audit.py`: hierarchy-based waiver ownership and independent
  frame-delta subtraction; a whole-frame bounding box is never used as an exception.
- `notebook/assets/chip/dot4/build.py` publishes the canonical stock artifacts;
  `frame_verify.py` executes the existing helper in a real Jupyter kernel and
  renders its output plus the KLayout raster in headless Chrome.

```bash
export PYTHONDONTWRITEBYTECODE=1
export TR1UM_PDK="$HOME/pdk/TR-1um-pinned"
export NGSPICE_BINARY="$HOME/.local/opt/tritflow-ubuntu-24.04/bin/ngspice"
python3 -B notebook/assets/chip/dot4/build.py --mpw-template "$HOME/TR-1um_MPW_Sanken"
python3 -B -m pytest tests/pnr tests/reuse -q \
  -o cache_dir=tests/pnr/.pytest_cache --basetemp=tests/pnr/.frame-tmp
```

PDK commit: `5d963db9d44e192d37a0489c208bfccf2e2f690c`.
Drawing SHA-256: `6d2453708f58a442dbf151d4afe6bb77d4c9f3e1b813807a781c6068a592f6dd`.
Mask SHA-256: `b5acaaa97f905947d23ca75fde9e32afba816ac24db48287c737c17a1260db7e`.
The final native chip qualification took 49.65 s, separate from macro P&R,
Jupyter and Chrome rendering. Electrical limits retain the existing DC-envelope,
sheet-R and width-scaling assumptions; no lifetime/package/transient claim is added.

## Final validation — complete

- **70 passed in 192.81 s** for `tests/pnr tests/reuse`, with the pinned PDK
  and specified Ubuntu ngspice binary. No failures or skipped requested checks.
- Native regression proves an added waiver is rejected even when placed exactly
  on a stock logo waiver, and preserves previous canonical GDS/metadata/reference
  bytes after failure. A changed mask inside the die/frame bounding box is also
  rejected; only the independently reproduced stock delta is accepted.
- Archive/source/artifact hash checks, strict ESD-inclusive LVS, 16-pad/frame
  checks, supply reserve and existing TEG/reuse flows all pass.
- Viewed `tr_1um_dot4.png`, `klayout_chrome.png`, and `shuttle.png` after final
  rendering. All sixteen pad nets, including the separate ESD_VDD, are readable.
- No remaining FRAME work, interface blocker, package installation, commit or push.
