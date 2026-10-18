# TritFlow: balanced-ternary HDL to GDS

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb)

Write balanced-ternary arithmetic in a Verilog-like HDL, inspect its cell
schematic, and follow it through synthesis, two-metal routing, PDK DRC/LVS and
extracted ngspice simulation. TritFlow runs on the open
[OpenSUSI TR-1um PDK](https://github.com/OpenSUSI/TR-1um) and lets you edit the
HDL and repeat the experiment in Colab.

![TritVerilog, mapped ternary cells, routed GDS and extracted waveforms.](figures/out/fig_flow.png)

The illustrated 4-trit adder maps to 64
cells in 1692 × 1590 µm, with 0 drawing-DRC
items and strict LVS Match (paper/adder4 · seed 7).

The electrical lesson is the middle level: ordinary CMOS and resistors make
a valid zero trit, but draw current while holding it. Predict the level and
current with a divider, compare sizing choices with SPICE, then see how cell
count and carry depth set an adder's power and settling time.

## Quickstart

Open the [notebook](notebook/tritflow_tr1um.ipynb) in Colab and choose
**Runtime → Run all**. Setup installs the tools and pinned public PDK and
prints the resolved source revision. The default run builds an opening adder
and an editable example; larger electrical studies are labelled recorded
results. If execution stops after setup, choose **Run all** again.

The published free-Colab record at
[6d8df9ef98135824198d1913fbfeada5a3f1c3a7](https://github.com/PenguinEino/tritflow/commit/6d8df9ef98135824198d1913fbfeada5a3f1c3a7)
completed all 18 code cells in 404.9 s, including setup, on the
first **Run all** in a fresh free runtime.
See the [run report](docs/status/COLAB.md).

For local use, keep the repository assets in an editable GitHub install:

```sh
python3 -m pip install --src ./src -e "git+https://github.com/PenguinEino/tritflow.git@colab-v0#egg=tritflow"
cd src/tritflow
bash notebook/colab_setup.sh --source "$PWD"
```

The setup script supports the Ubuntu amd64 releases listed in the
[setup guide](notebook/README.md). Native KLayout with Ruby DRC/LVS, ngspice
and the PDK are required; Python dependencies alone are insufficient.

From the source root after setup:

```python
from tritflow import flow
design = flow.load("examples/adder.tv", "adder", {"N": 2})
net = design.synthesize(name="adder2")
layout = net.place_and_route(output_dir="build/adder2")
assert layout.drc()["clean"] and layout.lvs()["matched"]
vectors = [tuple(0 for p in net.ports if p.dir == "input")]
post = layout.extract().simulate(vectors, load=100e-15)
```

This last line simulates one steady input state; inspect
`post["measurements"]` for its result. The notebook adds independent integer
oracles and labelled transition plans. `net.schematic(expand="*").show()`
displays the mapped circuit. Generated layouts, SPICE and reports go under
`build/`. Explore the [example circuits](examples/README.md) and
[use and extension guide](notebook/narrative/C_reuse.md) for the CLIs, STA,
new cells and operators.

## What is verified

- **Logic:** source-to-cell equivalence with its exhaustive or sampled scope;
  notebook arithmetic examples also use independent radix-integer references.
- **Physical design:** native PDK drawing DRC and strict device/connectivity
  LVS for the recorded layouts, with separate routing seeds identified in
  the notebook's evidence appendix.
- **Electrical behavior:** extracted-device SPICE checks output levels and
  final settling inside ±0.5 V for the stated inputs and loads;
  matched devices with/without estimated wire capacitance isolate that loading.
- **Recorded static timing:** 38/39 output maxima for
  matched transition sets are within ±20% of SPICE, with
  6.782% mean absolute percentage error. The separate conservative
  estimate averages 2.182× the measured maxima.
- **Optional framed top:** the canonical adder's MPW wrapper has
  0 mask-DRC items, strict drawing LVS Match
  and MPW precheck Pass. `layout.result.to_chip()` builds
  this separate top; its `signoff()` retains the physical reports.

Electrical results use nominal models and their documented input plans.
Wire capacitance is a geometry estimate; signal-wire resistance and coupling
are omitted. The framed top uses passive pads without ESD protection and is
awaiting allocation, bond/package and ESD approval plus final shuttle CI:
`submission_ready` is `false`. The
[scope appendix](notebook/narrative/A_limits.md) and
[evidence appendix](notebook/narrative/B_evidence.md) explain the conditions
and reruns.

The author taped out the original ternary cells in 2026;
silicon has not yet been measured. Return is expected in
January 2027. TritFlow adapts those circuits into an abuttable
cell library and supplies the HDL-to-layout flow and matched simulations.

## License and references

TritFlow is released under [Apache-2.0](LICENSE). Retain [NOTICE](NOTICE),
which credits the PDK and original circuits. The PDK is fetched separately
at its recorded revision and retains its own license and notices.

When citing or building on this work, identify the TritFlow source revision
and credit both underlying projects:

- **OpenSUSI, TR-1um open PDK**, based on TOKAI RIKA's IP62 process data;
  [repository](https://github.com/OpenSUSI/TR-1um),
  [qualified revision](https://github.com/OpenSUSI/TR-1um/commit/5d963db9d44e192d37a0489c208bfccf2e2f690c).
- **Einosuke Okazaki, opensusi-tr10-balanced-ternary-logic**, the original
  taped-out cell circuits and device sizes;
  [design repository](https://github.com/PenguinEino/opensusi-tr10-balanced-ternary-logic).

## Author

- Name: Einosuke Okazaki (岡崎 英之介)
- Affiliation: Information and Communication Engineering Course, Department of Monozukuri
  Engineering, Tokyo Metropolitan College of Industrial Technology (KOSEN), Tokyo, Japan
- Status: Fifth-year student (final year of the five-year KOSEN engineering programme, which
  combines upper-secondary and the first two years of tertiary education)
- Email: einosukeokazaki@gmail.com
- GitHub: PenguinEino

Prepared for the IEEE SSCS Code-a-Chip Travel Grant, ISSCC 2027.
