# tr_1um_dot4

Centered 2500 × 2500 µm die in the unmodified pinned PDK `OSS_FRAME`.
The 16 stock pads include 14 `OSS_ESD_5V_ANA`, one ESD VDD and one ESD VSS.

Core VDD = +5 V; VMID = 0 V; **ESD VSS = core VSS = substrate = −5 V**.
**ESD VDD is a separate +5 V terminal: apply it before or together with core VDD.**
Bond or probe all three core VDD pads; they join inside the die.
ESD VDD and core VDD are electrically separate inside the chip.

| Pad | Frame pin | Net | Pad cell | X (µm) | Y (µm) |
|---|---|---|---|---:|---:|
| P01 | P1 | VDD | OSS_ESD_5V_ANA | -200 | 1040 |
| P02 | P2 | VDD | OSS_ESD_5V_ANA | -600 | 1040 |
| P03 | P3 | x1 | OSS_ESD_5V_ANA | -1040 | 600 |
| P04 | P4 | x0 | OSS_ESD_5V_ANA | -1040 | 200 |
| P05 | P5 | w3 | OSS_ESD_5V_ANA | -1040 | -200 |
| P06 | P6 | w2 | OSS_ESD_5V_ANA | -1040 | -600 |
| P07 | P7 | w0 | OSS_ESD_5V_ANA | -600 | -1040 |
| P08 | VSS | VSS | OSS_ESD_5V_VSS | -200 | -1040 |
| P09 | P9 | x3 | OSS_ESD_5V_ANA | 200 | -1040 |
| P10 | P10 | w1 | OSS_ESD_5V_ANA | 600 | -1040 |
| P11 | P11 | y[1] | OSS_ESD_5V_ANA | 1040 | -600 |
| P12 | P12 | y[0] | OSS_ESD_5V_ANA | 1040 | -200 |
| P13 | P13 | VMID | OSS_ESD_5V_ANA | 1040 | 200 |
| P14 | P14 | x2 | OSS_ESD_5V_ANA | 1040 | 600 |
| P15 | P15 | VDD | OSS_ESD_5V_ANA | 600 | 1040 |
| P16 | VDD | ESD_VDD | OSS_ESD_5V_VDD | 200 | 1040 |

Remaining organizer steps:

- Allocate a complete 2500 × 2500 µm slot for this top.
- Agree the final bond diagram, including every supply bond and the VSS substrate.
- Complete the submission metadata/reference package and run the organizer's final CI.

Drawing DRC, strict device/port LVS including the ESD devices, MDP, mask DRC,
the copied organizer precheck and the DC width/cut reserve are recorded separately.
No post-MDP LVS stage is defined by the inspected organizer workflow.
Current limits use conservative engineering width scaling; this is not lifetime EM qualification.

## Qualification scope

The organizer's two stock 63/0 waiver polygons in `OSS_LOGO_TR` and `OSS_FRAME_CNR0` are preserved (union **63400 µm²**). There is **no TritFlow waiver geometry**, including inside the stock waiver area. The unchanged stock drawing and mask decks report **zero items**.

An independent frame-only MDP run reproduces the stock logo's **0.001508 µm² M2 XOR**. CO/M1/V1 XOR is zero everywhere; M2 XOR is **exactly zero outside that stock delta and on all macro/routing/pad/power geometry**. This applies the integrator's binding stock-frame policy; the full-die XOR is recorded, not hidden.

The programmable chapter 3–5 macro is byte-identical to the prior seed-0 GDS: **46 cells, 1692 × 1206 µm**. The fixed-weight edit (`dot4_fixed.tv`, 31 cells) remains a separate example.

| Supply | Core current envelope (mA) | Minimum DC reserve |
|---|---:|---:|
| VDD | 19.3616 | 31.1755% |
| VMID | 2.10094e-07 | 99.8718% |
| VSS | 19.3616 | 25.1964% |
| ESD_VDD | 0.001 | 99.7778% |

Every supply path includes a 1 µA auxiliary leakage budget. The pinned ESD MPE/MNE three-bias ngspice check at 27 °C measures at most 0.542608 nA summed absolute current. The DC model includes the actual 14 µm slotted-ring lanes/bridges, stock pad fingers, every added feeder/TC and macro rails. All modeled rectangles/cuts are checked against the GDS. A stock 70 µm pad TC uses conservative minimum-width scaling from the published 1.4 µm rating; this is an explicit engineering interpretation.

`native_signoff.json` and `evidence.zip` retain the native reports, independent stock-frame MDP, copied pinned decks and Sanken precheck/template, extracted device netlist, macro/chip metadata and reference. `provenance.json` hashes published artifacts, consumed qualification inputs and source files. The original Japanese helper archive remains for language-parity checking; its historical producer hashes are distinguished from the current sources.

Rebuild with `python3 -B notebook/assets/chip/dot4/build.py --mpw-template ~/TR-1um_MPW_Sanken` using the brief's PDK/ngspice environment. `frame_verify.py` renders the KLayout PNG/legend and `shuttle_view()` in headless Chrome. Notebook call: `from reuse import shuttle_view; shuttle_view()`.
