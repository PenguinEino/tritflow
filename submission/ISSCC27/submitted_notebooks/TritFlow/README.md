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
and [build information](build-info.json) accompany the notebook.

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

Chapter 6 of the saved notebooks ([English](tritflow_en.ipynb), [Japanese](tritflow_ja.ipynb)) contains the scaling,
power, timing, HDL-edit and framed-chip results with their conditions.

## Run in Colab

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PenguinEino/tritflow/blob/1104e9d27f2b4e938f1ae68b9e8427f2bbfa25a2/notebook/v3/tritflow_en.ipynb)

Open the primary notebook, connect a Python CPU runtime and choose **Runtime →
Run all**. Its setup cell obtains the full immutable `SOURCE_REF` from GitHub,
installs the open EDA tools and verifies the PDK archive checksum. Local files
and recorded campaigns are validated against the source and PDK before use.

Recommended: Python 3.12; KLayout binary/Python 0.30.6; ngspice 42 (Ubuntu package 42+ds-3build1); OpenSUSI TR-1um `5d963db9d44e192d37a0489c208bfccf2e2f690c`. Use the Python packages installed by the notebook bootstrap.

Saved outputs were executed locally; this v3 package has no claimed real-Colab Run-all verification.

For local execution, use the complete source checkout with the documented EDA
installation and pinned PDK. Open the corresponding `notebook/v3/` notebook,
or set `TRITFLOW_ROOT` to the checkout before running this copy.

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
