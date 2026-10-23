# TritFlow — balanced-ternary HDL to GDS on OpenSUSI TR-1um

IEEE SSCS Code-a-Chip, ISSCC 2027. Team: TritFlow

| Author | Affiliation | Email |
|---|---|---|
| Einosuke Okazaki (岡崎 英之介) | Information and Communication Engineering Course, Department of Monozukuri Engineering, Tokyo Metropolitan College of Industrial Technology (KOSEN), Tokyo, Japan | einosukeokazaki@gmail.com |

Fifth-year student (final year of the five-year KOSEN engineering programme, which combines upper-secondary and the first two years of tertiary education)
GitHub: [PenguinEino](https://github.com/PenguinEino).

Designated representative: **Einosuke Okazaki (岡崎 英之介)**.
Attendance/poster confirmation: **Einosuke Okazaki will attend ISSCC 2027 in person and present the poster if selected (confirmed by the author, 2026-10-18).**
The author of the historical balanced-ternary-logic project releases the derived schematic assets in this repository under Apache-2.0.

Ready for final submission review.

[English primary](tritflow_en.ipynb) — executed with saved outputs.

[Japanese companion](tritflow_ja.ipynb) — executed with saved outputs.

Read the saved schematics, tables, routed layouts and waveforms without a
kernel. Rerun for input selectors, sizing controls, routing replay and waveform
zoom. [Abstract](ABSTRACT.md), [pitch](PITCH.md), [official-rules checklist](CHECKLIST.md)
and [build information](build-info.json) accompany the notebook. The build
record identifies each notebook's source hash, immutable bootstrap pin, actual
execution commit, runtime versions and captured results.

## Why ternary, and what is new

Ternary-weight neural networks (e.g. BitNet b1.58) reduce the products of their linear
layers to sign selection, but the open ternary design tools we found build ternary arithmetic
from binary-encoded logic. TritFlow keeps every signal a single three-level wire from HDL to GDS:

- **Cells**: native three-level CMOS cells (−5, 0, +5 V, three power rails) adapted from the
  author's 1-trit multiply-add circuit taped out on the first OpenSUSI-MPW run; the notebook
  derives their functional completeness and checks the divider-held zero level against SPICE.
- **Flow**: a Verilog-like ternary HDL, equivalence-checked synthesis, a two-metal placer and
  router for three rails, PDK drawing DRC/LVS, extraction and post-layout ngspice.
- **Timing**: a ternary STA over six level transitions, compared with SPICE settling.
- **Results**: a dot product with one-trit weights and activations scaled to 16 terms (area, delay, wire load, STA
  accuracy, static power), an edit-and-rerun cell and an MPW-framed top.

## Concept and method

TritFlow implements balanced-ternary logic directly on the open OpenSUSI TR-1um
PDK. A trit takes −1, 0 or +1, represented by −5, 0 or +5 V. The cell library
comes from the author's taped-out 1-trit multiply-add circuit. A ternary-weight
dot product is the running design: the notebook explains its gates, writes
arithmetic in a Verilog-like HDL, checks synthesis equivalence, places and
routes cells, exports GDS, runs the PDK drawing-DRC and LVS decks, and simulates
the extracted devices with estimated wire capacitance in ngspice. Ternary STA
is compared with output settling times measured against the ±0.5 V bands.

## Results from this execution

| Executed check | Result |
| --- | --- |
| Synthesized dot product | 46 cells; 6,561 logical input vectors checked |
| Routed core dimensions | 1692 × 1206 µm |
| PDK drawing DRC | 0 violations |
| PDK LVS | Matched |
| Nominal post-layout SPICE | 11 stimulus intervals passed the ±0.5 V output-level check |
| SPICE maximum settling, y[1] | 133.6 ns |
| STA estimate, y[1] | 120.7 ns |
| SPICE maximum settling, y[0] | 227.4 ns |
| STA estimate, y[0] | 219.9 ns |

Logical input coverage and analog stimulus coverage are separate checks.
The numbers above are generated from outputs of the executed evidence cell;
no storyboard or hand-entered performance measurements feed this document.

From executed cell `c52`:

| Terms N | Output trits | INV | NAND | NANY | NOR | Input vectors checked | Equivalence |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 2 | 4 | 4 | 5 | 2 | Exhaustive 81 | Equivalent |
| 4 | 2 | 13 | 8 | 21 | 4 | Exhaustive 6,561 | Equivalent |
| 8 | 3 | 35 | 16 | 63 | 8 | Random 100,000 | Equivalent |
| 16 | 4 | 92 | 32 | 175 | 16 | Random 100,000 | Equivalent |

From executed cell `c52`:

| Terms N | Cells | Die size (mm × mm) | Die area (mm²) | Rows | HPWL (mm) | Routed length (mm) | Signal vias | Place and route (s) | DRC / LVS |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 15 | 0.61 × 0.87 | 0.53 | 5 | 3.95 | 8.27 | 107 | 1.73 | 0 / Matched |
| 4 | 46 | 1.69 × 1.21 | 2.04 | 6 | 24.30 | 40.44 | 329 | 2.98 | 0 / Matched |
| 8 | 122 | 2.16 × 3.05 | 6.60 | 13 | 167.86 | 236.37 | 1146 | 35.99 | 0 / Matched |
| 16 | 315 | 5.51 × 3.89 | 21.45 | 13 | 832.90 | 1,230.38 | 3320 | 48.55 | 0 / Matched |

From executed cell `c54`:

| Terms N | Cells | \|I(VDD)\| (mA · x=0) | \|I(VSS)\| (mA · x=0) | Static power (mW · x=0) | Time average (mW) | Static/cell (mW · x=0) | Average/cell (mW) | DC range (mW) | Hold time (µs/interval) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | 15 | 5.04 | 5.04 | 50.41 | 21.72 | 3.361 | 1.448 | 4.07–50.41 | 1.00 |
| 4 | 46 | 16.35 | 16.35 | 163.48 | 85.80 | 3.554 | 1.865 | 29.51–163.48 | 1.00 |
| 8 | 122 | 45.21 | 45.21 | 452.08 | 229.51 | 3.706 | 1.881 | 86.92–452.08 | 1.00 |
| 16 | 315 | 120.02 | 120.02 | 1,200.19 | 638.63 | 3.810 | 2.027 | 336.76–1,200.19 | 1.25 |

From executed cell `c56`:

| N | Output | STA, no wire C (ns) | STA, with wire C (ns) | Increase (%) | SPICE, no wire C (ns) | SPICE, with wire C (ns) | Increase (%) | STA error (%) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2 | y[1] | 56.2 | 62.9 | 11.9 | — | 80.0 | — | -21.3 |
| 2 | y[0] | 68.1 | 75.6 | 11.0 | — | 79.7 | — | -5.0 |
| 4 | y[1] | 106.1 | 122.5 | 15.4 | 113.1 | 128.6 | 13.7 | -4.8 |
| 4 | y[0] | 191.5 | 221.3 | 15.5 | 199.7 | 227.2 | 13.8 | -2.6 |
| 8 | y[2] | 363.3 | 462.2 | 27.2 | — | 432.3 | — | 6.9 |
| 8 | y[1] | 333.9 | 422.3 | 26.5 | — | 397.0 | — | 6.4 |
| 8 | y[0] | 348.3 | 437.0 | 25.5 | — | 440.2 | — | -0.7 |
| 16 | y[3] | 626.3 | 919.7 | 46.9 | — | 902.2 | — | 1.9 |
| 16 | y[2] | 596.9 | 880.5 | 47.5 | — | 868.6 | — | 1.4 |
| 16 | y[1] | 567.9 | 835.0 | 47.0 | — | 828.9 | — | 0.7 |
| 16 | y[0] | 576.2 | 839.3 | 45.7 | — | 828.6 | — | 1.3 |

From executed cell `c60`:

| Item | Result |
| --- | --- |
| Circuit | dot4_fixed |
| Cells | 31 |
| Macro size (µm) | 1284 × 1038 |
| DRC violations | 0 |
| LVS | Matched |
| SPICE input states | 11 / 81 (sampled states) |
| Output level and settling | PASS |
| Max. output error (V) | 0.0418 |
| y[1] max. settling time (ns) | 167.9 |
| y[0] max. settling time (ns) | 218.0 |
| Cell reduction from constant weights | 46 → 31 (−15, 32.6%) |

From executed cell `c62`:

| Check (recorded) | Result |
| --- | --- |
| Drawing DRC violations | 0 |
| Drawing LVS | Matched |
| Mask DRC violations | 0 |
| MPW precheck | PASS |
| Submission ready | False |

From executed cell `c62`:

| Pad | Signal / supply | Direction | X (µm) | Y (µm) |
| --- | --- | --- | --- | --- |
| P01 | VDD | power | -890.0 | 1100.0 |
| P02 | VDD | power | -78.0 | 1100.0 |
| P03 | VDD | power | 890.0 | 1100.0 |
| P04 | VSS | power | -700.0 | 1100.0 |
| P05 | VSS | power | 140.0 | 1100.0 |
| P06 | VSS | power | 732.0 | 1100.0 |
| P07 | VMID | power | 0.0 | -1100.0 |
| P08 | w0 | input | -1020.0 | -594.0 |
| P09 | x3 | input | -1020.0 | -444.0 |
| P10 | w1 | input | -1020.0 | -294.0 |
| P11 | w2 | input | -1020.0 | -144.0 |
| P12 | w3 | input | -1020.0 | 6.0 |
| P13 | x0 | input | -1020.0 | 174.0 |
| P14 | x1 | input | -1020.0 | 366.0 |
| P15 | x2 | input | -1020.0 | 558.0 |
| P16 | y[1] | output | 1020.0 | -594.0 |
| P17 | y[0] | output | 1020.0 | -402.0 |

## Run in Colab

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PenguinEino/tritflow/blob/28b0f02a3e38ed5a9b81c9c6d9710d9a611275b7/notebook/v3/tritflow_en.ipynb)

Open the primary notebook, connect a Python CPU runtime and choose **Runtime →
Run all**. Its setup cell obtains the full immutable `SOURCE_REF` from GitHub,
installs the open EDA tools and verifies the PDK archive checksum. Local files
and recorded campaigns are validated against the source and PDK before use.
The badge names the notebook's bootstrap pin; if the compatibility note below
reports a mismatch, publish a compatible source pin before sharing that badge
as the final reproduction entry point. No moving release tag is assumed.

Recommended: Python 3.12; KLayout binary/Python 0.30.6; ngspice 42 (Ubuntu package 42+ds-3build1); OpenSUSI TR-1um `5d963db9d44e192d37a0489c208bfccf2e2f690c`. Use the Python packages installed by the notebook bootstrap; exact observed versions for each execution are in build-info.json.

Saved outputs were executed locally; this v3 package has no claimed real-Colab Run-all verification.

For local execution, use the complete source checkout with the documented EDA
installation and pinned PDK. Open the corresponding `notebook/v3/` notebook,
or set `TRITFLOW_ROOT` to the checkout before running this copy. Cell, schematic
and characterization assets are in the source repository; the submission
folder omits tool distributions, PDK files and raw simulation trees. The
builder's default work directory is `submission/.build/submission_capture/`.

<details><summary>Source compatibility and execution provenance</summary>

Immutable source commit `8f77584a7d39be94b475fb4f2ddfc9be4a9ea190` matches the packaged notebook, allowing its commit-stamp line (local git-object check).

Observed execution source: [28b0f02a3e38ed5a9b81c9c6d9710d9a611275b7](https://github.com/PenguinEino/tritflow/tree/28b0f02a3e38ed5a9b81c9c6d9710d9a611275b7). Working-tree changes at packaging
are recorded separately; a commit ID does not establish a clean checkout.
Each notebook records its own runtime versions at execution. Export-library
versions describe packaging, including when a matching raw capture is reused.

</details>

## Limits

The results cover nominal model conditions and the documented input sequences;
exhaustive HDL equivalence does not establish exhaustive transistor-level
transition or PVT coverage. Wire capacitance is a geometry-based estimate,
without a calibrated PEX deck, signal-wire resistance or coupling extraction.
The cells use static current to establish ternary levels. Drawing DRC and LVS
verify their stated geometry and connectivity scope; a routed core alone does
not establish padframe, ESD, mask signoff or manufacturing readiness. Silicon
measurements of the taped-out source cells remain future work. This project
makes no performance or energy-efficiency claim against binary logic.

## License and references

Notebook, code and derived schematic assets are **Apache-2.0**. [LICENSE](LICENSE)
is the complete license and [NOTICE](NOTICE) preserves attribution. Einosuke
Okazaki (岡崎 英之介), author of the historical schematics, releases the derived assets
under Apache-2.0. External tools and the PDK retain their own licenses; their
distributions are not included or relicensed here.

- [TritFlow source and reproduction guide](https://github.com/PenguinEino/tritflow).
- [OpenSUSI TR-1um PDK](https://github.com/OpenSUSI/TR-1um).
- [Author's taped-out balanced-ternary cells and multiply-add](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic).
- [KLayout](https://www.klayout.de/), [ngspice](https://ngspice.sourceforge.io/),
  [Plotly](https://plotly.com/python/) and [Lark](https://github.com/lark-parser/lark).

The notebook includes its technical bibliography. Previous Code-a-Chip
submissions were consulted for presentation and folder structure; no notebook
cells or code were copied from those submissions.

## Filing

Copy **only this directory** to `ISSCC27/submitted_notebooks/TritFlow/` in a
fork of the [official repository](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io).
File the PR before **October 31, 2026, 11:59 AM Pacific Time**, and monitor
organizer feedback. Run `python3 submission/build_submission.py --check
--require-final` in the source checkout before filing. The package's 12 MiB
budget is a local convenience, not an official limit. This builder does not
commit, push or open the submission PR.
