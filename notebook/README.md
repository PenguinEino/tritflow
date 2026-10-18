# Submission notebook draft

[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb)

`tritflow_tr1um.ipynb` follows chapters 0–9 of `docs/concept.md`. Chapter 0
runs an actual two-trit adder from HDL through GDS, DRC, LVS and post-layout
ngspice. Logical coverage is exhaustive; its six analog states are explicitly
representative. The default run also includes NANY DC and an editable nine-state
small-circuit experiment. Gate, layout, animation, DC and transient figures use
the streams' public `tritflow.viz.*` functions.

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
python3 notebook/make_notebook.py
python3 notebook/validate_notebook.py
python3 notebook/validate_notebook.py --execute
python3 -m pytest tests/hdl tests/synth tests/viz notebook/tests -q
```

The executor compiles every code cell, checks chapters/IDs, and runs the same
code with headless Plotly serialization. It does not install anything locally.
`TRITFLOW_NOTEBOOK_BUILD` overrides `build/notebook`; `TRITFLOW_EXTENDED=1`
enables optional N=4 routing, route animation and additional loads. Notebook
caches include code/library/PDK hashes, package and tool versions, options and
produced artifact hashes. Cache hits identify the original verified artifacts;
they do not claim that checks ran again. Delete the cache to force a fresh run.
The checked-in notebook is output-free; `make_notebook.py` regenerates it.

Runtime inputs are committed under `cells/out/` (including the template,
characterization and verification reports), `examples/`, and
`notebook/assets/schematics/`. The notebook generates its own GDS, reports,
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
been removed. **Release TODO:** the integrator must publish the `colab-v0` tag
after committing these files; the badge targets that same tag.

```sh
bash notebook/colab_setup.sh --source /content/tritflow
# Non-mutating platform plans, usable locally:
bash notebook/colab_setup.sh --plan --ubuntu 22.04 --arch amd64
bash notebook/colab_setup.sh --plan --ubuntu 24.04 --arch amd64
```

Setup installs ngspice through apt; selects KLayout 0.30.6's official `.deb`
for the **detected** Ubuntu 22.04/24.04 amd64 release; installs its dependencies
through apt; pins the Python runtime dependencies; installs this package
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
The actual apt/pip install, notebook display in Colab, Ubuntu ngspice package
behavior, and install-inclusive cold runtime require a clean Colab test. Local
validation cannot establish the ten-minute Colab budget.

Remaining notebook TODOs are explicit: release-tag publication, public W/L
sizing-sweep support, the final qualified N/load/IR result matrix,
and final measurement hardware/schedule. No draft TODO is presented as a result.

The six taped-out source schematics are bundled under `assets/schematics/`,
each with an opaque light and dark SVG. Chapter 1 displays a theme-aware gallery
using embedded data URLs, so no Xschem installation is needed in Colab. The
manifest records source/dependency/exporter/output hashes and actual symbol
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
SVG text remain readable without host-page CSS.

The review pass removes hand-entered result counts from prose, derives coverage
and conditions in tables, and asserts cached/fresh pass flags equally. Published
characterization and qualification files are checked against their referenced
artifacts before their numbers are displayed. FILL's probe-based qualification
is labeled explicitly; it is not called a standalone strict LVS match. Both
the nominal fanout method and measurement scope come from the SIM JSON. Band
settling, finite-step resolution, sampled analog coverage and omitted RC/PVT/IR
effects remain explicit limitations. The exact requested SIM sizing API and
return schema are in `docs/status/FRONTEND.md`.
