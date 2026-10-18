# REVIEW — completed independent audit

**The frozen implementation passes its tests and default local notebook;
release reproducibility and verification gaps remain.** Ranked findings:
one release blocker, four major, three minor. No code or notebook was edited.

The commit actually cloned/tested is
**`37034be20dc02d8ee82d15170b955b6ef2777d70`**, 2026-10-18 09:03 UTC.
Other streams continued working. Later read-only comparison observed HEAD
`a7d6da281ae33f486c75907efaf3256090c18282`; the facade, extractor, cache, naming
and notebook-generator paths implicated below remained unchanged when checked.
Later timing/poly/diagnosis/signoff additions are outside the frozen suite.
See [clone hashes](../../logs/review/clone_manifest.json),
[concurrent delta](../../logs/review/concurrent_delta.txt) and
[full claims ledger](../../logs/review/claims_audit.md).

## Reproduction decisions

- Only this file and `logs/review/` are written in the shared checkout. The
  explicitly requested local clone is `/tmp/tritflow-review-wox2aqgy/source`.
  No checkout/reset/stash/commit is performed. Generated runs stay in scratch.
- Fresh Python 3.12 venv, pinned `notebook/requirements-colab.txt`, editable
  package, pytest, nbconvert and ipykernel. System ensurepip is unavailable, so
  `venv --without-pip` plus system pip's `--python <venv>/bin/python` installs
  into that isolated venv. No shared interpreter packages are changed.
- Fresh PDK archive at pinned commit
  `5d963db9d44e192d37a0489c208bfccf2e2f690c`; SHA-256 verified against
  `notebook/setup_pins.json`. No HOME PDK/reference files are modified.
- Host is Ubuntu 24.04/aarch64. The checksum-correct official Ubuntu 24.04
  KLayout 0.30.6 binary is amd64 and fails with `Exec format error`. Therefore
  the native runs use installed KLayout executable 0.30.9 and fresh Python
  klayout 0.30.6, plus installed ngspice 46+. This is explicitly not a clean
  amd64 Colab installation test.
- Run the whole `tests` **and** `notebook/tests` suite, and execute every
  notebook cell with nbconvert in its own venv kernel. `--allow-errors` preserves
  error outputs and lets later independent cells run; errors, not nbconvert's
  exit status alone, determine success.

Fresh dependency install took **20.54 s**; PDK download/extraction **6.04 s**.
PDK archive SHA-256 is
`003010a0f64fafb96acf5a0d18614c096d8faf6ade29e13af4bde54d85262769`.
Exact package versions are in [environment.json](../../logs/review/environment.json)
and [frozen requirements](../../logs/review/requirements_frozen.txt). The pinned
binary architecture failure is in [pinned_klayout.json](../../logs/review/pinned_klayout.json).

## Reproduction results

| Check | Result | Evidence |
|---|---|---|
| Whole suite, including notebook tests | **338 passed, zero failures/skips**, pytest **866.14 s**, process wall **866.45 s** | [log](../../logs/review/pytest.log), [JUnit](../../logs/review/pytest.xml) |
| Cold nbconvert | **31 cells / 16 code cells**, zero errors, wall **412.41 s** | [executed notebook](../../logs/review/executed.ipynb), [result](../../logs/review/notebook_result.json) |
| Warm nbconvert | Zero errors, wall **2.63 s**, all nine expensive stages hit | [warm notebook](../../logs/review/executed_warm.ipynb), [result](../../logs/review/notebook_warm_result.json) |
| Scaling/load publication slots | Both skipped with explicit stale-PDK TODOs | [stdout](../../logs/review/notebook_stdout.txt), [publication audit](../../logs/review/publication_audit.json) |
| Printed numerical table consistency | **188 scalar values agree** with full-precision JSON within rounding | [numeric audit](../../logs/review/numeric_claims.json) |
| Extra unwaived MDP → IP62 checks | adder4 **46 WAR06**, full_add **16 WAR06**; all external-input gates; both clean/submission_ready false | [signoff](../../logs/review/signoff.json) |

Cold execution recomputed all stages; its four-design block took **365.11 s**.
The test suite and other project streams ran concurrently, so wall times are
observations on this host, not a Colab/install-inclusive ten-minute guarantee.
The warm run also passed without `--allow-errors`. Its cache hits are recorded
evidence, not a new execution of DRC/LVS.

Warnings: both nbconvert runs emitted the kernel TCP-without-encryption warning.
Actual cold-notebook EDA logs contain no convergence/error warnings; their only
error-word hits are six informational `flag_missing_ports enabled` messages.
Pytest reported no warnings. The initial ensurepip failure and incompatible
amd64 executable were handled explicitly, not hidden with test skips.

Reproduce from the retained environment:

```sh
cd /tmp/tritflow-review-wox2aqgy/source
TR1UM_PDK=/tmp/tritflow-review-wox2aqgy/TR-1um-5d963db9d44e192d37a0489c208bfccf2e2f690c \
  /tmp/tritflow-review-wox2aqgy/venv/bin/python -m pytest tests notebook/tests -ra
```

Exact nbconvert commands/kernel/options are in the result JSONs. Scratch is
retained. `logs/` is git-ignored: preserve/attach review evidence for release.
The [final audit](../../logs/review/final_audit.json) confirms zero tracked-file
changes in the clone after execution, unchanged finding-related source paths,
and continued pinned-PDK rejection of both latest live publications.

## Ranked findings

### 1. BLOCKER for release — badge/bootstrap select an older notebook

**Location:** notebook cells 0/1/29; `notebook/make_notebook.py:30`, `:42`, `:62`.
**Owner: integrator with FRONTEND.**

Public `colab-v0` resolves to `89b484bb484ca26f8bb8e1d8cb7ec26cccbea269`, whose
notebook has **24 cells**, versus **31** reviewed here. The badge therefore
does not run the reviewed four-design/curated-circuit deliverable. Public main
advanced to `a7d6da2` during review, but the tag stayed old. The instruction to
“create colab-v0 after committing this notebook” is stale: that tag exists.
No clean-Colab result validates the reviewed release.

**Fix:** integrator publishes a new immutable final tag; FRONTEND updates the
badge/bootstrap/default-ref tests together. Execute that exact tag in clean
amd64 Colab and retain commit, versions, errors, figures and install-inclusive
time. A public-main update or local pass does not validate the tag. Evidence:
[public refs](../../logs/review/public_refs_final.txt),
`git show colab-v0:notebook/tritflow_tr1um.ipynb`.

### 2. MAJOR — missing unloaded power metal passes “strict ports” LVS

**Location:** `tritflow/extract/lvs.py:105`–`:124`; baseline
`docs/status/SIM.md:140`. **Owner: SIM; FRONTEND for facade physical proof.**

Deleting **all 432 µm² of INV's VMID M1 rail** from a scratch GDS still returns
`matched=true`, `strict_ports=true`, with `VMID` restored into extracted SPICE.
The unchanged baseline also matches. `_unused_pin` proves only that the reference
formal has no device load, not that a physical conductor/label exists. Thus the
comment/status wording “physically present” overstates the check. PNR's separate
generation-time connectivity check covers power geometry, but raw extraction
and `Layout.lvs()` do not rerun that proof after a GDS change.

**Fix:** require drawn rail/label/continuity evidence before formal restoration,
analogous to PNR's isolated-input proof; otherwise label the result device-only
and require physical port proof in the facade. Add deleted-VMID rejection.
Evidence: [spice probes](../../logs/review/spice_probes.json),
[reproducer](../../logs/review/probe_spice.py).

### 3. MAJOR — headline scaling/load data do not reproduce with setup's PDK

**Location:** notebook cell 25; `notebook/experiments.py:104`;
`results/{adder_scaling,full_add_load_sweep}.json:sources_sha256`;
baseline `docs/status/SIM.md:265`–`:337`. **Owner: SIM, integrator.**

All six widths and the load sweep hash the installed `lvs/01_Extract.lvs`, which
differs from the pinned public PDK. Both slots print TODOs and omit the plots in
the fresh run. The values are internally consistent recorded local results;
they are not current results of the distributed pinned flow. FRONTEND's later
handoff independently acknowledges the same mismatch; it is not resolved.

**Fix:** republish the measured matrix/load boundary/derived fits after
requalification with the pinned PDK, or deliberately update and validate the
distributed pin. Preserve actual consumed hashes. Add a clean-pinned-PDK check
that required final-publication slots do not become TODOs. Evidence:
[publication audit](../../logs/review/publication_audit.json), cold cell 25.

### 4. MAJOR — facade rejects valid circuits with unused inputs

**Location:** `tritflow/flow.py:150`–`:161`; notebook cells 23/28;
baseline `docs/status/PNR.md:174`. **Owner: FRONTEND.**

`module unused(input trit a,b,output trit y); assign y=~a; endmodule` synthesizes
and routes cleanly. `lay.lvs()` returns a mismatch for b. The existing public
`pnr.strict_lvs` matches and restores b after proving its isolated labeled M2
pad. `lay.extract()` therefore refuses a legal circuit through the advertised
method chain. PNR's handoff request remains unconsumed.

**Fix:** delegate `Layout.lvs()` to `pnr.strict_lvs` with actual PNR data/library,
retaining fingerprint checks. Test the full facade with an unused input and an
injected missing pad label. Evidence:
[interface probes](../../logs/review/interface_probes.json),
[reproducer](../../logs/review/probe_interfaces.py).

### 5. MAJOR — physical abstract changes do not invalidate notebook caches

**Location:** `notebook/cache.py:25`–`:29`; notebook cell 2;
baseline `docs/status/FRONTEND.md:372`. **Owner: FRONTEND.**

`runtime_fingerprint` omits `*.abstract.json` and the library manifest. Changing
an INV abstract from width 108 to 216 in an isolated probe leaves the fingerprint
**identical**. Pin access, M2/V1 obstructions and free tracks are PNR inputs;
correcting them can reuse an earlier physical PASS instead of rerouting.
Output artifact hashes do not cover these omitted inputs.

**Fix:** hash every consumed abstract, manifest and publication identity, with
relative filenames/content; add a real fingerprint test changing only
pin/obstruction metadata. Evidence: `abstract_cache` in
[interface probes](../../logs/review/interface_probes.json).

### 6. MINOR — accepted HDL names do not survive analog-flow naming

**Location:** `tritflow/sim/spice.py:53`–`:64`,
`tritflow/sim/bench.py:55`–`:58`, `tritflow/synth/writers.py:52`.
**Owner: SIM with FRONTEND.**

Inputs a and A are legal case-sensitive HDL and pass nine logical states, but
`net.simulate()` raises `ValueError: Input/output pins do not match`. The
synthesis writer encodes case collisions; SIM's separate `gate_spice` writes
raw names, and SPICE is case-insensitive.

**Fix:** share reversible naming across writer/reference/bench/probes, mapping
waveform/oracle keys back. Alternatively reject unsupported names with a located
HDL diagnostic and documented restriction before physical work. Evidence:
`case_names` in [spice probes](../../logs/review/spice_probes.json).

### 7. MINOR — opening demo never exercises its most-significant sum

**Location:** notebook cell 4; `notebook/make_notebook.py:139`–`:140`.
**Owner: FRONTEND.**

All six sequence entries keep `sum[1]` at ideal zero; `sum[0]` visits only zero/+1.
The MSB waveform is flat and its maximum settling time is zero. Exhaustive logic
is sound and analog coverage honestly says representative, but the chosen
sequence demonstrates neither rail-level restoration nor transitions at every
output.

**Fix:** add positive/negative single-digit cases and carry assert/release; assert
that every displayed output visits all three levels. Evidence:
[output coverage](../../logs/review/demo_output_coverage.json).

### 8. MINOR — presentation obscures schematic-to-layout understanding

**Location:** notebook cells 7/13; `notebook/schematics.py:26`–`:29`;
chapter-3 raster display in `notebook/make_notebook.py`.
**Owner: FRONTEND, consuming CELLS APIs.**

There are 1,623 prose words but 443 code lines, six expanded schematics, repeated
raw tables/dictionaries and long all-state plots. At the actual preview's
1000 px content width, INV fills most of a screen; several NAND/NOR screens
precede NANY. RR properties overlap symbols. The 700 px NANY raster lacks
legend/device/pin overlays; fine hatching obscures contacts. CELLS' tested
interactive mapping/abutment tools exist but are unused in the notebook.

**Fix:** expand only the selected primitive, move HA/FA drawings beside chapter
4, collapse raw stats/provenance, and use `cell_figure`/`device_mapping` with a
highlighted NANY current path. Keep full evidence beneath the main 20–30 minute
narrative. Actual gate/wave/schematic previews were inspected in a new Chrome
tab; user Colab tabs were untouched. Preview:
[figures.html](../../logs/review/figures.html).

## Claims, engineering and reader audit coverage

[The full claims ledger](../../logs/review/claims_audit.md) covers every notebook
cell and every section of CELLS/COLAB/FRONTEND/PNR/SIM status, including subsequent
handoffs. It maps claims to tests/assertions/data or explicit historical,
unverified or planned scope. Hand-entered historical timings/test counts and
ignored-build campaign evidence are identified rather than newly certified.
The 188 directly checked table values agree; pinned-PDK provenance is the main
quantitative gap.

Independent integer oracles are not mapped-netlist self-comparisons. FILL's
probe method, sampled versus exhaustive coverage, released Newton guesses,
whole-hold settling, uncalibrated top-net C, omitted child-only/poly/signal R,
ideal-rail transients, separate IR and absent PVT/silicon qualification are
generally stated accurately. No blanket DRC warning exclusion or mismatched
native device comparison was found in successful-check paths. Missing-rail
formal restoration is the substantive verification exception above.

Mask failure is a **material scope limit**, not a hidden drawing-DRC failure:
independent signoff retains every WAR06 item and reports false clean. Actual
I/O/frame/supply integration and exposed-gate resolution are necessary before
manufacturing readiness. No mask LVS is invented where the inspected flow
defines none. The notebook already disclaims padframe/ESD qualification.

Primary PDK cross-checks confirmed seven PDFs/109 pages and cited current,
resistor and capacitor tables (`logs/review/OS00_p*.txt`, `OS04_p7.txt`). Root
Apache-2.0 LICENSE, README upstream credits, copied-builder attribution and
source/SVG hashes exist. No specific stripped notice or licence violation was
established; this is an attribution audit, not a legal opinion.

## Done / remaining / interface requests

REVIEW is complete: scratch reproduction, whole suite, actual cold/warm
nbconvert, fault probes, unwaived mask checks, claims/numerical/technical audit
and browser reader review. No REVIEW process, HTTP server or preview tab remains
running. Scratch/evidence are retained. No user input is required.

Implementation requests remain with owners named in findings 1–8. Resolve
release/pinned-publication and physical-port/facade/cache issues, rerun the
integrated suite/notebook, and qualify the exact release in Colab. Concurrent
timing/diagnosis features need a subsequent review; the 338-test result applies
only to the explicitly cloned commit.
