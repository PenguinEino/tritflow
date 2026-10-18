# TritFlow notebook

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb)

`tritflow_tr1um.ipynb` follows chapters 0–9 of `docs/concept.md`. Chapter 0
runs an actual two-trit adder from HDL through GDS, DRC, LVS and post-layout
ngspice. Logical coverage is exhaustive; its labelled analog states exercise every output at all three levels and are
explicitly representative. The default run also includes INV DC, a precomputed sizing slider, the compact published
library/characterization tables, all four shared designs through matched
device-only/added-wire-C simulation, and one selected circuit from chapter 8.
The reading path follows EDITOR’s `narrative/` text and embeds eight static
paper figures from `figures/out/`. Public `tritflow.viz.*` and schematic APIs
provide the optional/live views; the sizing slider selects measured rows.
`paper_evidence.json` couples generated captions to the exact committed images
and measurements. Main chapters contain the story; Appendix A/B hold scope,
reports, actual runtime and rerun instructions.

The method chain is in `tritflow.flow`:

```python
from tritflow import flow

d = flow.load("examples/adder.tv", "adder", {"N": 2})
table = d.truth_table()
net = d.synthesize(name="adder2")
lay = net.place_and_route(output_dir="build/adder2")
assert lay.drc()["clean"]
assert lay.lvs()["matched"]
post = lay.extract().simulate([(-1,)*5, (0,)*5, (1,)*5], load=100e-15)
assert post["measurements"]["passed"]
```

Input order is the netlist's input-port order, with one trit per scalar bit.
`load` accepts `cells=`, `pdk=` and `klayout_binary=`. `loads` accepts notebook
source. `net` is GateNetlist-compatible; `net.simulate(...)` uses the pre-layout
cell subcircuits. `lay.result` retains the public PnrResult. `lay.extract()`
requires matched LVS and adds actual-GDS top-net substrate C by default;
`wire_c=False` selects device extraction alone. Extracted SPICE, capacitance
assumptions and native measurement dictionaries remain accessible. The wrapper
uses only public stream functions and never silently chooses a mock library.

For local validation with the existing PDK/tools:

```sh
export TR1UM_PDK="$HOME/pdk/TR-1um-pinned"
python3 notebook/make_notebook.py
python3 notebook/validate_notebook.py
python3 notebook/validate_notebook.py --execute
python3 -m pytest tests/hdl tests/synth tests/viz notebook/tests -q
```

The executor compiles every code cell, checks chapters/IDs, and runs the same
code with headless Plotly serialization. It does not install anything locally.
`TRITFLOW_NOTEBOOK_BUILD` overrides `build/notebook`; `TRITFLOW_EXTENDED=1`
enables routing replay and additional loads. `PNR_ROWS`/`PNR_ANNEAL_STEPS`
control chapter 0. Chapter 6 has opt-in fixed-row/effort/seed controls, showing
measured die dimensions, aspect, utilization and HPWL. Appendix B uses a compressed recorded adder4/full_add/mac1/mul1 campaign when
its consumed-source/PDK/options and every native-artifact hash match. It labels
that producer's tools and recorded checks; it never claims new local verification.
Missing/stale records trigger local regeneration. `TRITFLOW_FORCE_RUN=1` bypasses
the record and local stage caches. No pre-existing ignored build tree is needed.
Its small circuits visit all input states, while adder4 uses SIM's documented
carry/overflow/cancellation plan. Expected values are independent radix
arithmetic. Rail IR is a separate nominal-current/resistance estimate.
Notebook
caches include code/library/PDK hashes, package and tool versions, options and
produced artifact hashes. Cache hits identify the original verified artifacts;
they do not claim that checks ran again. Set `TRITFLOW_FORCE_RUN=1` before Run all or delete the cache to force a fresh run.
The final cell reports stage times and recorded PNR/LVS/pre/post-SPICE times.
The checked-in notebook is output-free; `make_notebook.py` regenerates it.

Runtime inputs are committed under `cells/out/` (including the template,
characterization and verification reports), `examples/`, and
`notebook/assets/` (schematics, portable paper evidence and recorded shared-design archive),
plus the embedded paper images from `figures/out/`. The
notebook generates its own GDS, reports,
SPICE, rasters and caches under `build/notebook/`; no existing `build/` is
needed. The taped-out reference repository and Xschem are needed only to
**re-export** the bundled SVGs, never to run the notebook.

To repeat the local portability check (requires strace and existing EDA/Python
tools; downloads a checksum-verified pinned PDK archive unless supplied):

```sh
python3 notebook/check_portability.py --workdir /tmp/tritflow-portability
# Optional: --pdk-archive /path/to/the/pinned-pdk.tar.gz
```

This exports only tracked working files into a new directory, with no `.git`
or ignored outputs; it records the base commit and file hashes. It uses no
git-writing command. Python audit guards reject original-checkout/reference
reads, and a native-child file trace must show zero accesses to those paths.
HOME remains unchanged; Python dependencies are reused, while the HOME tool
installation is relocated and its inherited search paths are removed. Logs,
the manifest and `report.json` remain in the work directory. This checks runtime
asset independence; it does not test Colab installation or replace the release
test after the integrator commits/tags the tree.

The first cell in a fresh Colab runtime shallow-clones
`https://github.com/PenguinEino/tritflow.git` at the default tag `colab-v0` into
`/content/tritflow`. It prints the resolved commit before installing the package
editably. Set `os.environ["TRITFLOW_REF"] = "another-tag"` before running the
first cell to override the tag (branch names also work; their resolved commits
are printed). An existing checkout is reused only when its origin and resolved
ref match and it has no tracked edits; otherwise start a fresh Colab runtime.
The notebook never silently falls back to `main`. The archive-URL bootstrap has
been removed. Source-selection and rerun details are in Appendix B of the notebook.

```sh
bash notebook/colab_setup.sh --source /content/tritflow
# Non-mutating platform plans, usable locally:
bash notebook/colab_setup.sh --plan --ubuntu 22.04 --arch amd64
bash notebook/colab_setup.sh --plan --ubuntu 24.04 --arch amd64
```

Setup installs ngspice through apt; selects KLayout 0.30.6's official `.deb`
for the **detected** Ubuntu 22.04/24.04 amd64 release; installs its dependencies
through apt; pins only klayout and lark; preserves Colab’s NumPy/SciPy/
Matplotlib/Plotly and checks their minimum versions; installs this package
editably beside its assets; and unpacks the PDK at commit
`5d963db9d44e192d37a0489c208bfccf2e2f690c`. The script verifies SHA-256 for
both binary and PDK downloads, checks required PDK/source files, and tests the
KLayout Ruby DRC engine. Unsupported OS/architecture fails explicitly. A
`runtime.json` supplies the notebook's environment before TritFlow is imported.
The script's default PDK destination is separate from any existing checkout.
The Python wheel alone does not provide the Ruby DRC/LVS runtime.

The official packages and their release mapping were checked against
[KLayout's download page](https://www.klayout.de/build.html). Pinned PDK source
is the [OpenSUSI commit](https://github.com/OpenSUSI/TR-1um/commit/5d963db9d44e192d37a0489c208bfccf2e2f690c).
The downloaded `.deb` hashes/package metadata and pinned archive contents were
checked locally; pinned-deck LVS and post-layout simulation passed locally.
A current Colab runtime note is withheld until the next successful real-Colab
Run all. Historical evidence remains in `docs/status/COLAB.md` and
`notebook/colab_verified.json`; `publish` is false for the historical record.

Required SIM publications use `load_grid()` / `sizing_figure()` for
`cells/out/sizing/`, `load_scaling()` / `scaling_figure()` for
`results/adder_scaling.json`, and `load_sweep_results()` / `load_sweep_figure()`
for `results/full_add_load_sweep.json`. Missing/stale publications stop execution. Cached W/L candidates expose adopted dimensions and a
selectable candidate's actual DC transfer/current curves; failed points retain
their flags. Expensive sizing, width scaling and load-boundary producers are
documented but not run by default. Published scaling/load records are checked
against relocated code/library/PDK source hashes, without requiring their raw
ignored build directories. They describe recorded runs rather than new checks.

Chapter 8 selects `sign`, `compare2`, `mul2` or `minmax` using `CHOICE` or
`TRITFLOW_CIRCUIT`. Each has an independent integer specification in
`examples/curated.py`, exhaustive source/mapped checks and a real physical
regression. Edited HDL and its includes are staged in the notebook build tree;
committed examples stay intact. A deliberately broken signal-arithmetic
expression prints its located HDL error and a repair hint. Every selected
circuit also runs extracted ngspice with all input states in the chosen order.
Its initial internal-node Newton guesses come from mapped logic and strict-LVS
net correspondence. The notebook displays those `.nodeset` values; no `.ic` or
`uic` constrains the transient. This avoids the nonphysical operating-point
root observed in the NOR-based sorter, while outputs still face the independent
integer oracle and unchanged acceptance band.

```sh
python3 -m pytest tests/synth/test_curated.py -q
TRITFLOW_CIRCUIT=mul2 python3 notebook/validate_notebook.py --execute
```



The six taped-out source schematics are bundled under `assets/schematics/`,
each with an opaque light and dark SVG. Chapter 1 expands one selected primitive in a theme-aware gallery
using embedded data URLs, so no Xschem installation is needed in Colab. The
HA/FA paper view is shared between chapters 4/5; extra native schematics are collapsed. The manifest records source/dependency/exporter/output hashes and actual symbol
counts. The gallery checks output hashes; the arithmetic chapter checks mapped
HA/FA counts against the source hierarchy counts.

```sh
python3 notebook/export_schematics.py
python3 -m pytest notebook/tests/test_schematics.py -q
```

Export uses batch Xschem on temporary copies of the six `.sch` files and every
referenced local/PDK/device symbol. Only absolute paths in those copies are
relocated. Source files and PDK symbols are never opened for writing. Primitive
crops omit stale free-text sizing sidebars while retaining actual instance
properties; color/stroke normalization changes presentation only. Source inputs
are hash-checked after export. The standalone light/dark variants and native
SVG text remain readable without host-page CSS. RR property text is shifted into empty space
without changing paths, terminal labels or values. Chapter 3 pairs the static cell/abutment hero with one labelled CELLS device-map view.
Chapter 8 exposes an HDL literal and regenerates its mapped schematic, actual GDS
and extracted waveform. Its independent oracle reports a counterexample before
routing when an edit changes the intended function.

The review pass removes hand-entered result counts from prose, derives coverage
and conditions in tables, and asserts cached/fresh pass flags equally. Published
characterization and qualification files are checked against their referenced
artifacts before their numbers are displayed. FILL's probe-based qualification
is labeled explicitly; it is not called a standalone strict LVS match. Both
the nominal fanout method and measurement scope come from the SIM JSON. Band
settling, finite-step resolution, sampled analog coverage, omitted signal
R/coupling/PVT and ideal-rail transient assumptions remain explicit limitations.
The exact requested SIM sizing API and
return schema are in `docs/status/FRONTEND.md`.


To publish the repeated four-design evidence after a successful full fresh run:

```sh
TRITFLOW_FORCE_RUN=1 TRITFLOW_NOTEBOOK_BUILD=/tmp/tritflow-full python3 notebook/validate_notebook.py --execute
python3 notebook/campaign.py /tmp/tritflow-full/cache
```

The publisher rejects stale runtime fingerprints or changed native artifacts.
`assets/four_designs.zip` contains native GDS/PNR/DRC/LVS proof and compressed
waveform/measurement JSON, with relative member names and a hash manifest.
Its separate publication fingerprint includes every consumed abstract, manifest
and publication identity, source and PDK. Cross-platform reading remains
**recorded evidence on the named producer tools**, not reuse of a local PASS.
The opening adder and selected chapter-8 circuit still execute physical and
analog work in a fresh session. Full characterization/sizing/scaling/load and
the repeated four-design matrix are the explicitly precomputed work.

To regenerate the recorded shared-design archive from a completed fresh capture
(with the same consumed inputs and native evidence still present):

```sh
TRITFLOW_FORCE_RUN=1 python3 submission/build_submission.py --workdir /tmp/tritflow-native
PYTHONPATH=. python3 notebook/campaign.py /tmp/tritflow-native/flow/cache
```

The explicit Python path also supports a source checkout that has not been
installed editably. Publishing rejects changed inputs, options or native bytes;
it does not repair a stale/failed run or claim new verification on replay.

Phase 9 setup uses pip `--no-deps`, so an already imported NumPy is not replaced.
Minimum host versions are NumPy 1.26, SciPy 1.11, Matplotlib 3.8 and Plotly 5.18.
Metadata checks, live/disk version comparison, the formerly failing NumPy-testing
import and a SciPy BLAS solve run before chapters. A mixed old kernel gets an
explicit restart-once instruction. Actual KLayout/ngspice executable versions
print even when setup is reused. The setup schema refreshes older runtime
configuration; it never silently reinstalls the scientific stack.

Each chapter cell checks setup and completed prerequisites. A failing rerun
invalidates downstream completion markers, so stale `lay`/`demo` globals cannot
masquerade as a successful prior result. Gates, characterization, sizing, cell
views, arithmetic, synthesis and the editable circuit can run after setup/imports
without the opening physical experiment. PNR/paired-waveform views request a
successful opening run; the wire-C overlay also requests the schematic cell.
The closing summary requests every prior cell.

Both direct `synth.synthesize(...)` and `flow.load(...).synthesize()` expose
`.schematic(**options)` through the shared synthesized-netlist class. Chapter 5
uses its hierarchical view and `expand="*"` half-adder view, with settled trits.
Chapter 7 calls `lay.result.net_parasitics()` and `.annotate(...)` on the same
schematic scene; annotations describe estimated routed wire C, not pin C or
calibrated PEX. Public SVG outputs remain vector images and receive PNG reading
fallbacks in the submission package.

For older width/load records, the reader discloses one exact source-compatibility
case: deleting only the new optional `.schematic()` delegate must recover the
complete recorded mapping-file SHA. Its AST must be the undecorated public
SCHEM forwarder; every other byte must match. This does not relabel the old
measurement as a new run. Any other mapping/report edit, or changed
HDL/library/PDK input, still fails. The fresh four-design archive uses the full
current source instead.

To refresh figure captions after the integrator publishes matching paper figures
and native results (this does **not** redraw the figures):

```sh
PYTHONPATH=.:notebook python3 notebook/paper_evidence.py
python3 notebook/make_notebook.py
```

The static source notebook is output-free. Build the compact saved-output copy
with `python3 submission/build_submission.py --workdir /tmp/tritflow-submission`.
Local execution and regression evidence accompany the capture. A real-Colab
runtime note will be published after the next successful verification.

Figure regeneration does not gate the flow. `load_paper` strictly checks the
recorded measurement inputs, while changed or missing presentation assets only
warn. After the integrator commits regenerated figures, refresh their hashes
without repeating any simulations:

```sh
python3 notebook/paper_evidence.py --refresh-presentation
python3 notebook/make_notebook.py
```

The generator uses dollar-delimited Markdown math with `\mathrm`, keeps equations
outside HTML Details, bounds embedded images to the text column, and wraps prose
tables. A new verified runtime note requires a successful real-Colab report and
explicit promotion of that new evidence. Local notebook execution never promotes it.
