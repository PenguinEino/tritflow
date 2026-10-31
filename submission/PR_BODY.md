## TritFlow: balanced-ternary HDL to GDS on Japan's first commercial open-source PDK (OpenSUSI TR-1um)

**Author / designated representative:** Einosuke Okazaki (岡崎 英之介), Tokyo Metropolitan College of Industrial Technology (KOSEN), Tokyo, Japan

TritFlow is an open design flow that takes a dedicated balanced-ternary HDL (TritVerilog) through logic synthesis, two-metal place and route, GDS, PDK DRC/LVS, post-layout ngspice and ternary timing analysis, using CMOS standard cells that keep every signal on three voltage levels (−5, 0, +5 V). The cells are based on ternary circuits the author taped out on the first OpenSUSI-MPW shuttle (OpenSUSI-TR10, chips expected January 2027).

- `tritflow_en.ipynb` (English) and `tritflow_ja.ipynb` (Japanese), both saved with outputs; `README.md`, `LICENSE` and the flow figure `tritflow_flow.png`.
- Run all on a fresh Colab CPU runtime takes about 13–15 minutes including setup; the notebook fetches the TritFlow source at a pinned commit of https://github.com/PenguinEino/tritflow (tag `isscc27-tritflow-submission`).
- Tools: Python 3.12, KLayout 0.30.6, ngspice 42, OpenSUSI TR-1um commit `5d963db`.
- License: Apache-2.0.

All files are inside `ISSCC27/submitted_notebooks/TritFlow/`; nothing outside the project folder is changed.
