# FRONTEND status

Updated: 2026-10-18. **Phase 8 review fixes implemented; pinned-publication integration and saved-output rebuild in progress.**

## Phase 8 handoff (in progress)

- Author fields now follow `docs/author.md` exactly, including student status and
  GitHub; no telephone field is included. The user has explicitly authorized
  Apache-2.0 for their derived historical schematic assets; submission licensing
  text reflects that authorization rather than requesting it again.
- REVIEW 4: `Layout.lvs()` delegates to `pnr.strict_lvs` with actual PNR data and
  a freshly loaded physical library. Reuse fingerprints include GDS, gate
  reference, PNR data, template, library/publication JSON, every abstract,
  cell SPICE and named LVS-deck contents. Inputs are checked before/after LVS.
  Real pinned-PDK unused-input synthesis/P&R/DRC/LVS/extracted-ngspice passes;
  deleting its actual TXM2 pad label invalidates the prior proof and blocks
  `extract()`. `Layout.signoff()` delegates to PNR's documented public method,
  retaining explicit clean/submission_ready flags and carried settings.
- REVIEW 5: notebook fingerprints hash relative filenames and content for every
  abstract, root manifest/publication JSON, physical/electrical views, source,
  decks/models and tools. A real INV abstract test edits only pin access or M2
  obstruction metadata, with unchanged GDS/SPICE; both invalidate. Manifest and
  generation edits invalidate; byte-identical relocation preserves the key.
- REVIEW 6 writer side: `spice_names`/`spice` are documented as the common
  reversible boundary already adopted by SIM. A writer/SIM contract regression
  covers a/A, y/Y, rail case and an encoded-prefix collision. No SIM/PNR files
  were edited; PNR owns decoding its physical-label/formal comparisons.
- REVIEW 7: chapter 0 uses labelled ± single-digit, carry assert/release and
  return vectors in elaborated port order. Every output, including sum MSB and
  carry, must visit all three ideal levels, actually change, and have measured
  nonzero settling in the analog result.
- REVIEW 8: only the selected primitive expands (NANY by default); HA/FA move
  beside chapter 4. Chapter 3 uses CELLS' public `cell_figure`, `device_mapping`
  and `row_abutment`, with labelled original/published devices and both devices
  of the Y→VMID clamp branch highlighted. Branch terminal topology and its
  measured DC state are asserted; highlights are not current-density data.
  Raw reports/conditions/provenance use collapsed controls. Static submission
  captures retain the selected schematic; runtime can expand alternatives.
- Runtime: prior capture metadata attributes 699 s of 789 s to the four-design
  loop; recorded PNR time was only a few seconds/design. New cache/stage and
  PNR/LVS/pre/post-SPICE timers will resolve the dominant analog work. The
  experiment helper reuses the official DRC report just produced by PNR,
  avoiding an identical second invocation. Cached reports remain labelled
  recorded evidence; `TRITFLOW_FORCE_RUN=1` or deleting the documented cache
  forces recomputation. No state coverage or SPICE accuracy was reduced.
- Required sizing/width/load publication slots now fail on missing/stale data
  instead of printing TODOs. Pinned cell-qualification deck hashes are also
  checked. Final Run all verifies that consumed inputs did not change during
  execution. Only public PDK `5d963db` at `$TR1UM_PDK` is used for qualification;
  reference SVG export tests now use `~/pdk/TR-1um-pinned` too.

Focused regression so far: 30 tests passed (31.61 s), before the added
presentation/demo tests. No extra packages, git-writing commands or foreign
path edits. Final notebook timings/publication coverage/package checks pending.

### Interface requests

SIM/CELLS/PNR: final capture requires republished pinned-PDK sizing, cell
qualification, width-scaling and load-boundary records with current consumed
hashes. The readers now require these records; they do not weaken provenance
or turn stale data into a result. The current live cell `verify_report.json`
still names the dev PDK and differs from pinned decks as of this intermediate
check. The release-ref mismatch from phase 7 remains an integrator action;
no tag or bootstrap write was performed here.

## Phase 7 handoff

Submission packaging is complete under the newly owned `submission/`, including
an actually executed notebook with saved outputs. No PR, push or git-writing
command was run. Identity/licensing confirmations and a matching published
source release remain submitter/integrator filing actions, as detailed below.

Official sources checked on 2026-10-18:

- Current official root README at commit
  `a502a6ba01260d3492df9137dddae0bb5fabeb3c`, ISSCC27's README and
  submitted-notebooks README, and the IEEE SSCS award page. Source URLs/hashes
  are recorded in `submission/official_sources.json`; the payload checklist
  links the exact revision plus the live IEEE page.
- The current target is `ISSCC27/submitted_notebooks/<project_name>/`; the
  deadline is **October 31, 2026, 11:59 AM Pacific**, not midnight.
  The older `howtoapply.md` names ISSCC26 and November 27, 2025, so its event/
  deadline are superseded. Its author-at-top, references and version guidance
  are retained conservatively and labeled as older presentation guidance.
- Read accepted ISSCC26 current-mode logic/CircuitsDNA and VLSI26 IMC
  side-channel folders, checking their event acceptance/winner lists. They
  illustrate notebook/README/license/support-file structure; no notebook/code
  was reused. No numerical file/byte limit or abstract/pitch requirement was
  invented as an official rule. Our seven-file / 8-MiB cap is a packaging guard.

Implementation:

- `submission/build_submission.py` executes the current notebook in a Jupyter
  kernel with real Plotly PNG export, saves all tables/results, normalizes
  machine paths, embeds the schematic gallery as native SVG/PNG bundles and
  validates source-cell identity, successful execution, evidence counts,
  file hashes and size. PNG optimization is lossless. Figures/measurements
  are never replaced with hand-entered values. Animation captures are labeled
  as stills; normal re-execution restores interactive figures.
- Payload target: `submission/ISSCC27/submitted_notebooks/TritFlow/`.
  Only seven files belong in the eventual official-repository PR: notebook,
  README, LICENSE, ABSTRACT, PITCH, CHECKLIST and build-info JSON. Full source,
  PDKs, library trees, caches, raw SPICE/waveforms and build tools stay out.
  A successful capture publishes from validated staging; failures retain raw
  diagnostics outside the payload. `--from-executed` supports packaging edits
  without pretending to run EDA again; `--check` audits the saved package.
- `submission/team.json` contains explicit name/affiliation/email/team/
  representative placeholders. No suggested personal identity was inferred.
  Generated README and notebook front matter draw from that file. The
  historical schematic repo had no separate license file when inspected, so
  included-export rights are a submitter confirmation field rather than an
  invented license claim. Root TritFlow Apache-2.0 LICENSE is copied verbatim;
  external tool/PDK licenses and reference provenance remain separate.
- One-paragraph abstract, exactly three-sentence pitch, and official-rule
  mapping are in reviewable templates and copied into the payload. The
  checklist distinguishes included technical evidence from pending identity,
  filing, attendance/poster/travel documentation and deferred Colab actions.
- **Release prerequisite:** a read-only remote query found `colab-v0` at
  `89b484bb484ca26f8bb8e1d8cb7ec26cccbea269`. That release lacks
  `notebook/experiments.py` (and predates the present notebook). The builder
  records local release/source compatibility and adds a concrete README/front-
  matter TODO when mismatched. Integrator must publish a corresponding
  immutable source ref and configure `TRITFLOW_REF` before filing. Bootstrap
  code remains unchanged; no tag was created/moved here. Saved reading does
  not require that runtime release to be ready.

Validation: **7 packaging tests pass in 0.42 s**, including checks against the
actual generated payload, decoding every PNG, and rejecting active JavaScript,
missing execution evidence and unexpected files. `build_submission.py --check`
passes: **7 files, 1,850,638 bytes; 16 executed source code cells, 73 saved
outputs, 23 PNGs and 28 HTML tables**. Source notebook cells are unchanged;
submission identity/abstract/version front matter is added only in the copy.
The combined command
`python3 -m pytest notebook/tests tests/hdl tests/synth tests/viz submission/tests -q`
passed **234 tests in 45.68 s** before the seventh packaging test was added;
the final focused suite above includes that additional real-payload test.
`git diff --check` passes for the owned submission/status paths. Visual review
of the generated graph, waveform and full-adder schematic confirmed readable
static output; schematic bundles also retain native SVG for zooming.

The real capture completed all source code cells without errors in **788.98 s
(13.1 min)**, including static image export and nine fresh expensive stages
(adder flow/raster, NANY DC, pre-layout, four-design post-layout loop and the
selected min/max circuit), while other streams were running CPU-heavy jobs.
This is a local timing observation, not a Colab or under-ten-minute claim.
Raw execution evidence is retained outside the payload at
`/tmp/tritflow-submission-phase7/executed.raw.ipynb`. An initial post-execution
host import failure was fixed in the builder; the successful raw capture was
then reused with `--from-executed` for packaging, without another EDA run or
any fabricated outputs. The final package records this capture's duration,
source hash and bootstrap commit separately from packaging metadata. Tool
versions are explicitly labeled as observed at packaging because the raw
capture does not contain a separate version snapshot. Colab verification
remains postponed by instruction, and the bootstrap is unchanged.

Build-only packages installed using the required user pip command:
nbformat 5.10.4, nbclient 0.10.4, Kaleido 1.5.0, Choreographer 1.4.0,
CairoSVG 2.8.2 and their Python dependencies. Existing Chrome/Cairo were used;
no system packages or browser were installed. Kaleido 1.1.0 was initially
tested, found incompatible with the current Choreographer, and replaced by
the recorded 1.5.0 pin before capture. These dependencies are outside the
reviewer payload and do not alter the Colab bootstrap.

## Phase 6 handoff

Implementation and local notebook/circuit validation are complete. The Colab
bootstrap code cell is byte-identical to phase 5 / committed
`23f27e20455b29b7abf6d2ce166cd3f2f9c927e0`. Colab verification is postponed
by instruction. No git-writing commands or edits to other streams' files.

- Chapter 3 derives every library dimension/area/free-M2 count from the current
  publication and asserts that all cell heights, template and generation agree.
  No compact-library result number is copied from a status table.
- Chapters 0/6 expose automatic or fixed `rows`, `anneal_steps`, seed and an
  opt-in floorplan experiment. Actual dimensions, aspect, utilization, physical
  rows and recorded HPWL/placement/routing history are displayed. Auto sizing
  includes independently fed power spans; fixed row counts can reduce density.
- Chapter 2 checks recorded cascade source hashes/pass flags and derives
  measured receiver counts, chain depth, worst chain/driver settling and worst
  level error from `char.json`. Largest tested fanout is explicitly a nominal
  measured bound, not a PVT/general path guarantee.
- Chapter 7 synthesizes and physically regenerates adder4/full_add/mac1/mul1
  under the notebook's own output tree. SIM's public `representative_vectors`
  and `arithmetic_oracle` define the experiments. `notebook/experiments.py`
  chains public flow/P&R/extraction/SIM functions for official DRC, strict LVS,
  actual-GDS wire C, matched pre/post stimuli and separate geometry-based IR.
  All small-design input states are checked; adder4's coverage is labeled as
  sampled/directed arithmetic. Timing deltas compare the same transition.
- Publication slots remain explicit. Available W/L grids use
  `tritflow.sim.sizing.load_grid(cell)` and
  `tritflow.viz.scaling.sizing_figure(result)`; the adopted dimensions and a
  selectable candidate's true DC transfer/current curve are shown. The
  `sweep_dimensions` signature below is now implemented by SIM. Missing/stale
  grids print a TODO and no fabricated result.
- Scaling/load slots use `tritflow.sim.scaling.load_scaling(path)` with
  `scaling_figure(result)` and
  `tritflow.sim.load_sweep.load_sweep_results(path)` with
  `load_sweep_figure(result)`. They activate for
  `results/adder_scaling.json` / `results/full_add_load_sweep.json` when
  published, retaining failed widths, failed loads and null delays. Their
  current code/library/HDL/PDK source hashes are checked after path relocation;
  raw ignored build trees are provenance, never plotting dependencies.
  Missing/stale records remain clearly marked TODOs. Heavy producers are
  documented opt-in calls, not part of default Run all.
- Chapter 8 provides four choices in `examples/curated.py`: existing `sign`
  and `minmax`, plus new `compare2.tv` and `mul2.tv`. The comparator returns the
  sign of the difference of two signed two-trit integers; multiplication uses
  four scalar products and two half adders. Independent references use integer
  comparison/multiplication, balanced-radix encoding and sorting. The reader
  chooses `CHOICE` or `TRITFLOW_CIRCUIT`, sees exhaustive source/mapped checks,
  then runs physical checks and extracted ngspice. Edited HDL and includes are
  copied under the notebook output directory; committed examples stay intact.
- A deliberate `a+b` signal expression displays the real located `HDLError`
  and an operator-specific repair hint before physical work. The parser's
  existing diagnostics already supply filename/line/column, so no parser change
  was needed.
- Chapter 8's sorter initially exposed a nonphysical BSIM operating-point
  root despite correct logic and DRC/LVS. Diagnostics remain under
  `/tmp/tritflow-notebook-phase6/your_circuit/minmax/{pre,post}`. Through SIM's
  public `nodeset` argument, selected circuits now initialize internal Newton
  guesses from mapped trits, with extracted names obtained from the strict LVS
  cross-reference. These are released `.nodeset` guesses, never `.ic`/`uic`,
  device changes or relaxed acceptance. The actual guesses are displayed.
  Independent arithmetic still checks every output. The seeded sorter passed
  both pre/post probes; source and extracted decks/logs are under
  `/tmp/tritflow-minmax-seeded/`.
- Cached pre/post pairs now restore nested NumPy waveform arrays correctly.
  Cache context includes notebook helpers and example/reference code. Saved
  pass flags and artifact hashes are checked as well as fresh producer checks.

Phase 6 validation so far:

```sh
python3 -m pytest tests/synth/test_curated.py -q
python3 notebook/make_notebook.py
python3 -m pytest notebook/tests tests/hdl tests/synth tests/viz -q
TRITFLOW_NOTEBOOK_BUILD=/tmp/tritflow-notebook-phase6 python3 notebook/validate_notebook.py --execute
```

The four catalog designs passed all independent exhaustive checks and real
synthesis/P&R/official DRC/strict LVS: **8 tests passed in 16.19 s**.
The initial combined suite passed **195 tests in 20.05 s**, including nested cache
restoration, edited shared includes, and portable publication-source validation.
The final suite passed **228 tests in 23.82 s** (including the newly available
CELLS visualization regressions); no skips. After the final portable-reader
adjustments, its focused regressions passed **2 tests in 0.19 s**.

The **31-cell default notebook passed every chapter in 392.8 s locally**,
excluding installation, with all nine expensive cache stages computed fresh.
This includes both adder widths used in the narrative, every shared design's
official DRC/strict LVS/matched pre/post checks, and the default min/max sorter.
Log: `/tmp/tritflow-notebook-phase6-final.log`; generated artifacts/caches:
`/tmp/tritflow-notebook-phase6-final/`. This is a local cold runtime measurement,
not a Colab or installation-inclusive guarantee.

The actual chapter-8 cells were also executed with `TRITFLOW_CIRCUIT` set to
each remaining choice. All independent exhaustive source/mapped checks,
physical checks and complete selected pre/post input-state sequences passed:
sign **4.69 s**, compare2 **123.35 s**, mul2 **344.89 s**. Log:
`/tmp/tritflow-choices-phase6.log`; artifacts are in the same output tree.
The multiplier is the most expensive selection; changing choices reuses the
common notebook stages when their context/artifacts are unchanged. Its full
analog sweep is outside the default min/max Run all timing above.

SIM published its grids, scaling and load-boundary records during this work.
The final publication-reader adjustment recognizes both relocated repository
names and PDK PDF provenance (`openIP62/`). A fresh execution of the actual
publication-slot cell loaded/checked **both current result JSONs** and serialized
their figures successfully: `/tmp/tritflow-publications-phase6.log`. The full
notebook's earlier pass had honestly left TODOs while those fingerprints were
changing. No raw `build/` evidence was needed to display the published data.

Pinned-PDK provenance check: the official PDFs exist in the pinned archive,
but current SIM scaling/load records hash the installed
`libs.tech/klayout/tech/lvs/01_Extract.lvs`, which differs from commit
`5d963db9d44e192d37a0489c208bfccf2e2f690c`. Both readers correctly reject a
current-result claim against that pinned copy. **SIM/integrator request:**
republish these measured records using the bootstrap's pinned PDK before
expecting their slots to appear as current in Colab. The explicit TODO remains
until provenance matches; no result hashes or measurements were rewritten by
FRONTEND. This does not block the requested notebook scaffolding or local
physical/arithmetic validation. Full Colab verification stays postponed.

The Colab bootstrap cell remains byte-identical to phase 5. Notebook generation,
syntax/chapters, owned-path `git diff --check`, cache restoration and circuit
include editing checks pass. Other streams continued committing/editing in the
shared checkout; no foreign changes were reverted. No git-writing command ran.
No packages installed.

## Phase 5 handoff

**Complete:** git-based Colab bootstrap, notebook badges and clean tracked-tree
runtime verification. This supersedes the phase 4 archive-publication TODO.
Root README and other streams' files were not edited. No git-writing command
was run; the integrator owns committing, tagging and pushing.

- The standalone first cell shallow-clones
  `https://github.com/PenguinEino/tritflow.git` with `--depth 1 --single-branch
  --branch colab-v0` into `/content/tritflow`. `TRITFLOW_REF` overrides the
  tag/branch name. The clone's resolved commit is printed before installation.
  The existing setup installs it using `pip install -e /content/tritflow`.
- Existing Colab clones must have the expected origin, matching resolved ref
  and HEAD, and no tracked edits. Otherwise the cell requests a fresh runtime;
  it never fetches/resets somebody's working tree or falls back to `main`.
  The optional archive-URL path was removed as permitted in phase 5, avoiding
  two source-provenance paths. Local notebook execution does not clone or
  install anything.
- Both `notebook/README.md` and the notebook introduction contain an Open in
  Colab badge targeting `colab-v0`. Recommended **root README** Markdown for
  the integrator (the badge becomes usable after that tag is published):

  ```markdown
  [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb)
  ```

- Runtime cell/GDS/SPICE/characterization/qualification inputs are tracked in
  `cells/out/`; `cells/template.json` is a relative tracked symlink to the
  tracked `out/template.json`. HDL examples/includes and the six light/dark
  schematic assets/manifest are tracked too. The notebook regenerates its own
  P&R, extraction, simulation, raster and cache files from an absent `build/`.
  It never runs the optional reference-dependent schematic exporter.
- `notebook/check_portability.py` exports only tracked working files, records
  their hashes and base commit, freshly extracts the checksum-verified pinned
  PDK, relocates the HOME KLayout distribution, removes inherited tool search
  paths, and executes every notebook chapter. Python audit guards reject
  reads from the original checkout and HOME PDK/reference/tool directories;
  strace checks native children for any accesses to those paths. HOME itself
  is unchanged and installed Python dependencies remain available.
- Decision: a tracked working-tree export replaces the requested local git
  clone because streams must not run git-writing commands. No `.git`, ignored
  outputs or untracked helpers are copied. Pending tracked frontend edits are
  included, so this tests the proposed notebook rather than just committed
  HEAD. This is an asset-portability test, not a kernel filesystem sandbox.
  User namespaces were unavailable (`bwrap`: UID-map permission denied).

Phase 5 validation:

```sh
python3 notebook/make_notebook.py
python3 notebook/validate_notebook.py
python3 -m pytest tests/hdl tests/synth tests/viz notebook/tests -q
python3 notebook/check_portability.py --workdir /tmp/tritflow-portable-phase5-clean --pdk-archive /tmp/tritflow-pdk-pinned.tar.gz
```

**184 tests passed in 7.24 s.** Tests execute the actual standalone bootstrap
cell with git mutations/install commands intercepted: default/overridden ref,
shallow clone arguments, printed commit, setup invocation, existing-clone
reuse, dirty/mismatched checkout rejection and missing-tag failure. Both
Ubuntu setup plans and the generated notebook structure remain checked.

The clean tracked-tree run passed all **24 cells / chapters 0–9** in **51.54 s**
under file tracing, excluding installation/staging. Initial `build/` was
absent; all five expensive stages ran fresh. Full-flow DRC/LVS, extracted
adder analog assertions, independent logical checks, source/asset hashes and
the editable circuit's full input-state test passed. The trace contains **zero
accesses** to the original checkout, `~/balanced-ternary-logic`, `~/pdk` or
`~/bin/klayout`. The first attempt completed the notebook but its audit caught
inherited PATH/LD_LIBRARY_PATH references to the original tool installation;
the successful run removes those inherited paths.

Evidence: `/tmp/tritflow-portable-phase5-clean/{report.json,tracked-files.json,
execution.log,files.strace}`; regenerated outputs:
`/tmp/tritflow-portable-phase5-clean/tritflow/build/notebook/`.
Export: **631 tracked working files**, base commit
`b91bd90bedeaaedd66f0484ea648686332eae76c`; the manifest records the tested
working-file hashes (later documentation-only changes are outside that snapshot).
Fresh PDK: `5d963db9d44e192d37a0489c208bfccf2e2f690c`, archive SHA-256
`003010a0f64fafb96acf5a0d18614c096d8faf6ade29e13af4bde54d85262769`.
Local tools: KLayout executable **0.30.9**, Python klayout **0.30.6**, ngspice
**46+**. Therefore this run does not validate the pinned official 0.30.6 Ubuntu
binary or Colab's apt ngspice, installation/display behavior, or the
installation-inclusive ten-minute budget. No packages were installed.

Read-only `git ls-remote` confirmed public `main` at the base commit above;
`colab-v0` was absent at verification time, as expected. **Integrator release
action:** commit the frontend changes (including new portability/bootstrap
test scripts), create/push `colab-v0`, then run the badge in a fresh Colab
runtime. The default intentionally fails until the tag exists. The separate
W/L sizing and final N/load/IR matrix TODOs remain unchanged.

## Phase 4 handoff

**Complete:** exported the six requested taped-out Xschem drawings, integrated
chapter 1, reviewed all chapters as a skeptical circuit-design reviewer, and
defined the SIM sizing interface below. Publication configuration is unchanged;
the integrator will provide its URL later.

- `notebook/export_schematics.py` runs native batch Xschem on temporary copies
  of `inverter.sch`, `mul_nand.sch`, `mul_nor.sch`, `nany.sch`, `half_adder.sch`
  and `full_adder.sch`. Every referenced local, PDK and system device symbol is
  copied into that temporary library path. Only absolute path locators in the
  copies are relocated. No Xschem invocation opens the original schematic.
  Input/dependency hashes are checked again after export.
- `notebook/assets/schematics/` contains `INV.svg`, `NAND.svg`, `NOR.svg`,
  `NANY.svg`, `half_adder.svg`, `full_adder.svg`, plus a `.dark.svg` variant
  of each and `manifest.json`. SVG geometry/text are the Xschem output;
  presentation changes normalize stroke/color and add accessible titles.
  Opaque high-contrast backing makes both variants independent of host CSS.
  The theme foreground/background contrast exceeds 7:1 in automated checks.
- Primitive crops omit obsolete free-text sizing sidebars in the reference
  schematics (e.g. old RR length notes). Actual instance W/L labels remain.
  The source is not edited to repair those historical annotations. Hierarchical
  drawings retain the explanatory circuit text and original wiring.
- `notebook/schematics.py` embeds all six drawings as a theme-aware data-URL
  gallery in chapter 1, with a both-themes/provenance control. Display requires
  no Xschem installation. The manifest records renderer, source, symbol and
  output hashes, crop bounds and generated counts of each source symbol.
  Chapter 4 independently checks RTL HA/FA gate counts against those counts.
- All 12 variants were rasterized locally with the installed librsvg/cairo
  libraries; primitive and HA/FA previews were visually inspected. Contrast,
  complete SVG path/text content, source preservation, deterministic re-export
  and gallery hash checking have automated tests. No packages were installed.

Reviewer changes:

- Removed hand-entered coverage/gate-count result numbers from prose. Coverage,
  unique states, possible/selected transitions, cells, physical area, errors,
  loads, timing settings and temperature now come from data or configuration.
  Trit equations and supply/measurement definitions remain explicit.
- Added independent gate truth assertions and both HA/FA integer invariants.
  Printed mapping examples are synthesized and asserted against the expected
  cell sequences; their displayed counts are calculated.
- Fresh and cached reports both face explicit pass assertions. Characterization
  source/model hashes and all recorded DC/transient pass flags are checked.
  Published cell qualification flags are shown only after referenced artifact
  hashes match. FILL is labeled as probe-based qualification, not a standalone
  device-free strict LVS match.
- Updated obsolete fanout text: the current JSON reports measured self-loading/
  cascade evidence, whose method, conditions and scope are displayed directly.
  No isolated-C ratio or synthesis default is presented as a general timing bound.
- The routing chapter shows actual clean flags, routed-net coverage, legal
  orientations and initial/final HPWL. It says optimization *seeks* shorter
  connections rather than asserting a global/minimum HPWL result.
- Pre/post checks assert matched stimuli/hold/step and show a load-derived title.
  Settling is explicitly the sampled/interpolated final band entry from ramp
  start. Sampled analog coverage, initialization exclusion, ideal rails,
  uncalibrated substrate C, omitted poly/signal RC, PVT and missing IR results
  remain limitations. The editable circuit asserts complete input-state coverage.
- Historical schematics are not presented as new-layout or silicon-performance
  proof. Measurement hardware/schedule, final N/load/IR matrix, W/L sweep and
  fresh Colab verification remain explicit TODOs.
- Confirmed the publication/bootstrap code cell is byte-identical to committed
  HEAD; `TRITFLOW_ARCHIVE_URL` / `TRITFLOW_ARCHIVE_SHA256` behavior was untouched.

Phase 4 validation:

```sh
python3 notebook/export_schematics.py
python3 notebook/make_notebook.py
python3 -m pytest notebook/tests tests/hdl tests/synth tests/viz -q
TRITFLOW_NOTEBOOK_BUILD=/tmp/tritflow-notebook-phase4-final python3 notebook/validate_notebook.py --execute
```

Result: **178 tests passed in 12.72 s**. The revised default notebook executed
all chapters successfully in **56.7 s** locally, excluding installation. Its
fresh full-flow assertions and the new source/model/qualification checks passed.
Log: `/tmp/tritflow-notebook-phase4-final.log`; assets/EDA outputs are under
`/tmp/tritflow-notebook-phase4-final/`. This remains a local runtime measurement,
not a Colab installation-inclusive claim.
An unchanged-context repeat passed every chapter in **0.7 s**, with all five
expensive stages reporting cache hits; log:
`/tmp/tritflow-notebook-phase4-warm.log`. The gallery, source/qualification
hashes and cached-result assertions were still evaluated on that repeat.

### Requested chapter 2 SIM function (exact proposal)

Please expose this in `tritflow.sim.sizing` (re-export from `tritflow.sim` is
optional). The computation should not import notebook code.

```python
def sweep_dimensions(
    cell: str,
    candidates: Sequence[Mapping[str, Mapping[str, float]]],
    *,
    sweep_pin: str = "A",
    fixed_trits: Mapping[str, int] | None = None,
    start_v: float = -5.0,
    stop_v: float = 5.0,
    step_v: float = 0.1,
    temperature_c: float = 27.0,
    pdk: str | Path | None = None,
    workdir: str | Path | None = None,
    timeout: float = 120.0,
) -> dict:
    ...
```

Semantics and units:

- `cell` is INV/NAND/NOR/NANY. Each candidate is a sparse device-ID map:
  `{device_id: {"w_um": value, "l_um": value}}`. Use canonical schematic IDs
  from `tritflow.cells.circuits.circuits()` (`MP`, `MN`, `RP`, `RN` for INV;
  the corresponding per-device names for other cells), exposed in the result.
  Omitted devices/dimensions inherit the published schematic baseline. Unknown
  IDs/fields, nonpositive dimensions and invalid trit biases raise ValueError.
- Both MOS and resistor W/L are in **µm**; no implicit scaling of unrelated
  devices or connectivity changes. Build temporary source-level SPICE variants;
  never mutate published cells, extracted junction geometry or PDK/source files.
  This is a DC sizing experiment, not a generated-layout/LVS qualification.
- Automatically include the adopted published baseline once, resolving its
  dimensions from the source rather than requiring hand-entered marker values.
  Return its index so the plot can mark the adopted point unambiguously.
- Run the input-voltage transfer sweep with other inputs at `fixed_trits`
  (default zero); separately evaluate all discrete trit input states for maximum
  level error and true static rail currents. Supplies/band use project constants.
  `workdir` retains artifacts only when supplied; times/timeout are seconds.

Requested return schema:

```text
cell, source_sha256, model_sha256, device_ids, adopted_index,
conditions {supplies_v, temperature_c, band_v, sweep_pin, fixed_trits,
            start_v, stop_v, step_v},
rows [
  {dimensions: fully resolved device W/L in µm, is_adopted: bool,
   transfer: native dc_transfer-compatible data/log result,
   dc: native dc_operating_points rows,
   max_error_v: float | null,
   max_static_current_a: float | null,
   passed: bool, error: str | null}
],
scope: "nominal source-level DC sizing; no layout/parasitic/PVT qualification"
```

Use native numeric arrays or JSON numeric lists for transfer data; the notebook
can convert lists back to NumPy before the existing transfer figure helper.
Return solver failures as failed rows with null unavailable metrics and a
diagnostic; never drop them or turn them into passing points. The adopted
index must refer to the same resolved baseline dimensions as the source hash.
This is a requested interface, **not** an implemented/exported function yet;
the chapter 2 TODO remains until SIM supplies it.

Phase 3: **flow API and notebook draft complete**. Clean Colab execution and
publication metadata are explicitly pending, as detailed below.

## Phase 3 handoff

- `tritflow/flow.py` implements the requested chain:
  `flow.load(path, top, params).synthesize().place_and_route()` followed by
  `.drc()`, `.lvs()`, and `.extract().simulate(vectors, load=...)`.
  `Circuit.truth_table()` delegates to the HDL simulator. `flow.loads()` accepts
  editable source; `net.simulate()` uses pre-layout cells; `flow.load_layout()`
  reopens public PNR artifacts without inventing fresh verification evidence.
- The facade calls only public HDL/synth, PNR `Library.load` /
  `place_and_route` / `pdk_drc` / `PnrResult`, extraction `extract_layout` /
  `gds_wire_capacitance` / `append_wire_capacitance`, and SIM `gate_spice` /
  `simulate` functions/classes. It does not modify another stream's code or
  substitute mock cells. Native reports/waveforms remain exposed. Unmatched
  LVS blocks post-layout simulation. A recent in-memory LVS result is reused
  only while GDS/reference/deck and extracted/report hashes remain unchanged.
- `notebook/tritflow_tr1um.ipynb` is a 24-cell, output-free English draft with
  chapters 0–9. Chapter 0 runs a two-trit adder through real-cell synthesis,
  GDS, DRC, LVS, actual-GDS wire C and ngspice, with an independent integer
  oracle. All 243 logical inputs are checked; six analog states are explicitly
  representative, not exhaustive transitions. The draft includes gate graphs,
  KLayout GDS raster, physical net highlighting, placement history, DC curves,
  pre/post waveforms and an editable nine-state circuit experiment.
- The newly delivered public `tritflow.viz.layout` and `tritflow.viz.waves`
  functions are integrated. No missing-visualization placeholders remain.
  Chapter 2 sizing/SVGs and the final N/load/IR result matrix have clearly
  marked TODO cells. These draft gaps are not presented as measured results.
- `notebook/cache.py` caches expensive stage dictionaries as gzip JSON, with
  hashes of code, library GDS/SPICE/characterization, PDK decks/models, package
  and executable versions, stage options and produced artifacts. It restores
  waveform arrays and stimulus tuples without pickle. Changed inputs/artifacts
  invalidate results. Failed producers do not publish a successful cache entry.
- `notebook/make_notebook.py` regenerates the notebook exactly.
  `notebook/validate_notebook.py` validates IDs/chapters/code and can execute
  every cell locally with headless Plotly serialization. No local install is
  performed by that executor. Usage is in `notebook/README.md`.
- `notebook/colab_setup.sh` wraps the tested Python setup planner/installer.
  It detects Ubuntu and amd64, installs ngspice via apt and the matching
  official KLayout 0.30.6 `.deb` via apt, installs pinned direct Python runtime
  dependencies plus this package editably, and unpacks the PDK at commit
  `5d963db9d44e192d37a0489c208bfccf2e2f690c`. It validates binary/archive
  SHA-256, archive paths/links and required source/PDK assets. It runs a real
  Ruby DRC-engine smoke macro and writes environment settings before notebook
  imports. No existing PDK checkout is overwritten. `--plan` is non-mutating;
  Ubuntu/architecture overrides are permitted only in plan mode.

Phase 3 checks:

```sh
python3 -m pytest tests/hdl tests/synth tests/viz notebook/tests -q
python3 notebook/validate_notebook.py
TRITFLOW_NOTEBOOK_BUILD=/tmp/tritflow-notebook-final python3 notebook/validate_notebook.py --execute
bash notebook/colab_setup.sh --plan --ubuntu 22.04 --arch amd64
bash notebook/colab_setup.sh --plan --ubuntu 24.04 --arch amd64
```

- **175 tests passed in 7.71 s**, including a real INV PNR/DRC/LVS/wire-C/
  ngspice facade regression, public-function delegation, mismatch rejection,
  cache invalidation, platform planning, checksum rejection, safe archive
  links/traversal and notebook generation/compilation. Other streams added
  visualization tests concurrently; the selected suite includes them.
- The complete default notebook executed locally in **46.1 s**, excluding
  installation (the local setup cell correctly does not install). All default
  analog checks passed. The two-trit post-layout maximum sampled error was
  **0.04334 V**. Its exported die was **840 × 2022 µm** for the library state
  used in that run. Logs are `/tmp/tritflow-notebook-final-cold.log` and caches/
  physical artifacts are under `/tmp/tritflow-notebook-final/`.
- A repeat run encountered changed library/code files from parallel work and
  correctly invalidated the old context. Cache hit/option/artifact invalidation
  behavior is separately covered by deterministic unit tests. Report runtime
  figures with the library/PDK state; do not freeze stale files to force a hit.
- Separately exercised the actual one-trit/27-vector and two-trit representative
  adder chains. DRC clean, matched LVS and post-layout band checks passed.
- Downloaded both official Ubuntu 22/24 `.deb` files and verified SHA-256 plus
  Debian package/version/architecture metadata. The PDK commit archive was
  downloaded, hashed and extracted with the setup's own safe extractor. Its
  public pinned LVS deck and models passed local two-trit extraction/LVS and
  post-layout simulation. Installed/local PDK `run.lvs` has a different include
  ordering comment; the pinned public deck was tested independently rather
  than assumed identical. The Ruby engine smoke macro also passed locally.
- No packages installed. No git state mutations. PDK and taped-out source
  checkouts were read only. Only authorized FRONTEND/notebook paths were edited.

**Unverified in Colab:** actual apt dependency resolution, pip installation in
the clean Colab interpreter, its ngspice package's convergence, interactive
notebook display, and total download/install-inclusive cold/warm runtime.
The ten-minute Colab goal remains a validation target, not a measured claim.

Phase 2 follow-up: **complete**. Standard CLI builds, notebook gate graphs,
HTML truth tables, expanded mapping docstrings and their tests are delivered.

## Phase 2 handoff

- `python3 examples/build_all.py` now produces the standard synthesis artifacts
  through the public CLI in `build/adder4/`, `build/full_add/`, `build/mac1/`,
  and `build/mul1/`. Each contains `<top>.json`, `<top>.gate.tv`, `<top>.spice`,
  `<top>.report.json` and `<top>.report.txt`. The actual four builds were run
  successfully in the checkout; all source-to-cell equivalence checks passed.
- The script resolves the repository from its own path, so it works from any
  working directory. `--output-root PATH` permits isolated builds. It replaces
  only synthesis outputs and does not delete other streams' artifacts. Tests
  build twice via subprocesses from outside the repo, compare SHA-256 hashes
  for all 20 artifacts, and check that a PNR marker survives.
- `tritflow/viz/graph.py` provides the following direct-import APIs, without
  changes to any other visualization module:
  - `gate_graph(net, inputs=None, *, title=None) -> plotly.graph_objects.Figure`
  - `color_nets(net, inputs, *, title=None) -> Figure`
  - `net_values(net, inputs) -> dict[str, int]`
  - `truth_table_html(design_or_net, *, max_rows=81) -> str` with `_repr_html_`
- Graphs use longest-path logic levels left-to-right, stable barycenter ordering
  within each level, arrows, and distinct port markers. Gates retain cell-type
  fills. Net coloring uses blue/gray/red for -1/0/+1 with a complete three-value
  legend including ideal voltages. Hover includes cell, source hierarchy,
  output value and pin values. Each signal net gets a trace, including unused
  primary input stubs. Plain loaded GateNetlist objects and arbitrary instance
  order work; plotting does not mutate the source netlist or global renderer.
- The pandas-free truth table accepts source or mapped designs, escapes names,
  labels port direction, and displays every input vector. It rejects excessive
  row counts before evaluation (81 rows by default), rather than truncating.
- Added the backward-compatible `evaluate_netlist(..., return_all=True)` option
  for internal nets, so the graph and notebook analysis reuse the cell evaluator.
  Default results still contain only output ports. Graph coloring requires
  scalar trits for all bit-blasted inputs; batched analysis uses the evaluator.
- Expanded package/API docstrings in HDL and synth explain settled trit values,
  vector ordering, the elaboration pipeline, NAND/NOR fusion, positive min/max
  extra inversion, NANY saturation, TIE mapping, primitive preservation, fanout,
  logic depth, and the limits/modes of equivalence checks for an IC reader.
- New notebook examples are in `examples/README.md`. No new packages installed;
  existing Plotly 7.1.0 is used.

Phase 2 validation:

```sh
python3 examples/build_all.py
python3 -m pytest tests/hdl tests/synth tests/viz -q
```

Result: **157 passed in 1.96 s**. Figure trace colors, levels, full internal-net
coverage, hover data, legends, invalid-input rejection, constants, unused inputs,
HTML escaping, size guards, and arithmetic table contents are covered. A
standalone full-adder Plotly HTML preview was exported to
`/tmp/tritflow-full-add-graph.html`. Browser visual inspection could not run
because no connected browser is available; figure schema/HTML export and
semantic checks passed. This does not block the delivered APIs/builds.

Notebook example:

```python
from tritflow.netlist import GateNetlist
from tritflow.viz.graph import color_nets, truth_table_html

net = GateNetlist.load("build/full_add/full_add.json")
color_nets(net, {"a": 1, "b": 1, "cin": -1}).show()
truth_table_html(net)  # notebook rich HTML; 27 complete input vectors
```

## Done

- Lark parser with a source-located AST and `file:line:column` diagnostics.
  ANSI ports, inherited port types/ranges, vectors, selects, concatenation,
  constants, integer parameters/localparams, named connections/overrides,
  generate loops (including nested loops), and all five gate primitives work.
- Hierarchical elaboration resolves parameters, bit-blasts vectors, flattens
  hierarchy, and retains source hierarchy/location on DAG nodes. It detects
  multiple drivers, undriven used nets/outputs, combinational cycles (including
  dead driven logic), recursive hierarchy, invalid widths/indices, and
  nonterminating generate loops.
- `tritflow.hdl.load`, `loads`, `parse`, `elaborate`, `Design.evaluate` /
  `simulate`, and `truth_table` provide the notebook API. NumPy evaluation
  supports scalar values and broadcast input arrays and validates trits before
  casting. The module docstring distinguishes trits from Verilog four-state logic.
- Ternary-safe constant folding, double-negation elimination, idempotence,
  constant bounds/identities, nany-with-zero simplification, structural hashing,
  dead-code removal, and cost-reducing De Morgan transformations. No Boolean
  complementation/excluded-middle rules. Rewrites are exhaustively tested over
  ternary inputs, with a further deterministic corpus of composed expressions.
- INV/NAND/NOR/NANY/TIE mapping; explicit live primitive instances preserve
  their cell identity. Balanced BUF trees enforce the configurable fanout
  bound (default 4) on every cell input pin, including repeated pins.
- Independent cell-level simulation validates the mapped netlist, including
  its drivers and acyclicity. Synthesis automatically compares the original
  unoptimized source DAG against cells: all 3^n vectors for n<=12, otherwise
  100,000 reproducible random vectors. Input vectors stream in batches.
- Shared GateNetlist JSON, parseable gate-level TritVerilog, top-level SPICE,
  and JSON/text reports (cells, cell-stage depth, exclusive per-hierarchy cell
  counts, maximum fanout, equivalence evidence). CLI is implemented.
- HA, FA, parameterized adder, MUL, MAC with taped-out auxiliary AND/OR
  buffers, minmax, and sign examples. Arithmetic tests use integer references
  independent of gate equations. Every small example is exhaustively checked;
  the parameterized adder is exhausted for N=1..5 and N=6 is checked against
  100,000 additional independent arithmetic vectors.
- [Examples and API guide](../../examples/README.md).

## Decisions

- Explicit primitive instances preserve their authored cells, even with constant
  inputs; unused gates are removed. Expression logic is optimized separately.
  This retains the reference HA/FA gate counts and source hierarchy.
- A relative `` `include "file.tv" `` extension allows examples to share the
  reference HA/FA definitions. Source errors retain included file locations.
  `load` can alternatively take a list of source paths.
- Expression/assignment widths must match exactly; gate primitives are scalar.
  There is no implicit width extension or truncation. Vectors and concatenations
  use declared left-to-right/MSB order; arithmetic weights bit i by 3^i.
  Integer division truncates toward zero and remainder follows that quotient.
- Fanout means the number of connected cell input pins. External output
  capacitance belongs to SIM characterization. Limits below 2 are rejected
  because BUF trees cannot split a load with fanout 1.
- Distinct output aliases use BUF cells to preserve public net names while
  satisfying the one-driver shared contract. Source inputs are not renamed.
- Global signal net names VDD/VMID/VSS are rejected, matching the shared power
  contract and PNR validation. SPICE encodes punctuation and case conflicts
  deterministically and records original names in comments. Its signal order
  is A[, B], Y followed by VDD VMID VSS; the testbench supplies cell/model includes.
- De Morgan transformations are deliberately conservative: negative lattice
  expressions already mapping to NAND/NOR are not expanded. Structural hashing
  retains deterministic source operand order for reproducible artifacts.
- `SynthesizedNetlist` subclasses the unchanged integrator-owned GateNetlist to
  supply `report()`. Only top/ports/instances are serialized as shared JSON.
- CLI `-P N=4` appends `4` to the top and artifact name (`adder4`); `--name`
  overrides this. Python synthesis preserves `design.top`. Materialized truth
  tables default to at most 12 inputs; automatic equivalence streams batches.

## Validation and output examples

Run from the repository root:

```sh
python3 -m pytest tests/hdl tests/synth -q
python3 -m tritflow.synth examples/adder.tv --top adder -P N=4 -o /tmp/tritflow-frontend-adder4/
```

Result: **137 passed in 1.11 s** (Python 3.12; no extra packages installed).
The CLI was exercised directly and in subprocess tests, including diagnostic
exit paths. All example gate files are parsed again and compared to the original
netlists. All JSON files are loaded through the shared GateNetlist loader.
SPICE pin order, rail suffixes, TIE cells and case/punctuation encoding are tested.

| Example | Cells | Depth | Exhaustive input vectors |
|---|---|---:|---:|
| half_add | NANY=5, INV=2 | 6 | 9 |
| full_add | NANY=11, INV=5 | 12 | 27 |
| adder, N=4 | NANY=44, INV=20 | 27 | 19,683 |
| mul1 | NAND=2, NOR=1, INV=1 | 3 | 9 |
| mac1 | NANY=11, INV=9, NAND=2, NOR=1 | 15 | 81 |

The direct CLI run produced `adder4.json`, `adder4.gate.tv`, `adder4.spice`,
`adder4.report.json`, and `adder4.report.txt` under the temporary directory above.
Representative `adder4.report.json` fields:

```json
{
  "top": "adder4",
  "cells": {"INV": 20, "NANY": 44},
  "total_cells": 64,
  "logic_depth": 27,
  "max_fanout": 3,
  "fanout_limit": 4,
  "equivalence": {"passed": true, "mode": "exhaustive", "vectors": 19683, "seed": null}
}
```

Frontend validation establishes logical equivalence. Device behavior, timing,
DRC/LVS and parasitics remain the owning streams' checks.

## In progress

None.

## Blockers

None.

## Interface requests

1. **Integrator — release:** phase 5 supersedes the archive-URL request. Commit
   and push these files, publish `colab-v0` in the public TritFlow repository,
   add the recommended badge to root README, and verify a clean Colab launch.
   The bootstrap defaults to that tag and prints its resolved commit.
2. **SIM — sizing chapter: resolved in phase 6.** The exact requested API and
   cached grids are available and integrated conditionally. Publication slots
   retain explicit missing/stale TODOs, including the scaling/load boundary.
   **Pinned provenance follow-up:** regenerate scaling/load publications with
   bootstrap PDK commit `5d963db9d44e192d37a0489c208bfccf2e2f690c`; the current
   installed `01_Extract.lvs` hash differs, as documented in the phase 6 handoff.
3. **Schematic assets: resolved in phase 4.** All requested SVGs are bundled and
   integrated; no asset request remains with another stream.

No interface is missing for the core flow method chain. Shared contracts and
other streams' source files were not edited by FRONTEND.

## Extra dependencies installed

None. Existing lark 1.3.1, numpy 2.4.3 and pytest were used.
