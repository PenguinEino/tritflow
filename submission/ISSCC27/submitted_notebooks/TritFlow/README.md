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

Development package. English primary notebook is not yet available; this is a Japanese development preview. tritflow_ja.ipynb: pinned release does not contain the same notebook and required helpers. tritflow_ja.ipynb: local execution used a different commit from the bootstrap pin. tritflow_ja.ipynb: execution used unpublished changes to runtime inputs. tritflow_ja.ipynb: chapter 6 evaluation has not executed in this source revision.

[Japanese development preview](tritflow_ja.ipynb) — executed with saved outputs.

Read the saved schematics, tables, routed layouts and waveforms without a
kernel. Rerun for input selectors, sizing controls, routing replay and waveform
zoom. [Abstract](ABSTRACT.md), [pitch](PITCH.md), [official-rules checklist](CHECKLIST.md)
and [build information](build-info.json) accompany the notebook. The build
record identifies each notebook's source hash, immutable bootstrap pin, actual
execution commit, runtime versions and captured results.

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
| SPICE maximum settling, y[1] | 133.5 ns |
| STA estimate, y[1] | 120.7 ns |
| SPICE maximum settling, y[0] | 227.4 ns |
| STA estimate, y[0] | 219.9 ns |

Logical input coverage and analog stimulus coverage are separate checks.
The numbers above are generated from outputs of the executed evidence cell;
no storyboard or hand-entered performance measurements feed this document.

This executed revision contains no chapter 6 evaluation; scaling and power results are not reported here.

## Run in Colab

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PenguinEino/tritflow/blob/71ba7253326c140441893f6be2752803d8fb51c9/notebook/v3/tritflow_ja.ipynb)

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

The local source-ref check found `71ba7253326c140441893f6be2752803d8fb51c9` at `71ba7253326c140441893f6be2752803d8fb51c9`. The local notebook differs from that pinned release. Build-info.json records the checked source-ref details. Before filing, the integrator must publish a source pin compatible with the final notebooks.

Observed execution source: [4361c38e1506621346e8e0a48f26f126899e335e](https://github.com/PenguinEino/tritflow/tree/4361c38e1506621346e8e0a48f26f126899e335e). Working-tree changes at packaging
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
--require-final` in the source checkout before filing. The package's 8 MiB
budget is a local convenience, not an official limit. This builder does not
commit, push or open the submission PR.
