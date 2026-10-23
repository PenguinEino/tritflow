# TritFlow — balanced-ternary HDL to GDS on OpenSUSI TR-1um

IEEE SSCS Code-a-Chip, ISSCC 2027. Team: {{TEAM_NAME}}

{{AUTHORS_TABLE}}

{{AUTHOR_DETAILS}}

Designated representative: **{{REPRESENTATIVE}}**.
Attendance/poster confirmation: **{{ATTENDANCE}}**
{{ASSET_RIGHTS}}

{{PACKAGE_STATUS}}

{{NOTEBOOKS}}

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

{{RESULTS}}

Logical input coverage and analog stimulus coverage are separate checks.
The numbers above are generated from outputs of the executed evidence cell;
no storyboard or hand-entered performance measurements feed this document.

{{CHAPTER6_RESULTS}}

## Run in Colab

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)]({{COLAB_URL}})

Open the primary notebook, connect a Python CPU runtime and choose **Runtime →
Run all**. Its setup cell obtains the full immutable `SOURCE_REF` from GitHub,
installs the open EDA tools and verifies the PDK archive checksum. Local files
and recorded campaigns are validated against the source and PDK before use.
The badge names the notebook's bootstrap pin; if the compatibility note below
reports a mismatch, publish a compatible source pin before sharing that badge
as the final reproduction entry point. No moving release tag is assumed.

{{RUNTIME}}

{{COLAB_RUN_NOTE}}

For local execution, use the complete source checkout with the documented EDA
installation and pinned PDK. Open the corresponding `notebook/v3/` notebook,
or set `TRITFLOW_ROOT` to the checkout before running this copy. Cell, schematic
and characterization assets are in the source repository; the submission
folder omits tool distributions, PDK files and raw simulation trees. The
builder's default work directory is `submission/.build/submission_capture/`.

<details><summary>Source compatibility and execution provenance</summary>

{{RELEASE_STATUS}}

Observed execution source: {{SOURCE_LINK}}. Working-tree changes at packaging
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
