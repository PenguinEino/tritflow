# REVIEW — round 3

Reviewed **`c84145b1ed66a37a87fe0c4ffb091a405e2d4034`**, then `colab-v0`, from a clean
local clone at `/tmp/tritflow-review3-1vofg_n6/source`. Read the binding editorial plan
first, then AGENTS, concept, interfaces and REVIEW brief. Cell indices below are zero-based;
source and submitted notebooks have the same indices through cell 32.

**Verdict: the story and numerical results now fit Code-a-Chip, but this revision is not
ready to submit.** A fresh notebook run fails before chapter 0, and actual Colab renders
the prediction equations as raw commands. These are concrete release/presentation faults.
The main scientific numbers reconcile with their data; the remaining teaching problem is
an unexplained prediction with the opposite sign to SPICE.

The shared checkout advanced to **`1885903850972457955b640554e966b98f72736d`** during review,
and FRONTEND is changing the presentation/evidence helpers. Those changes are outside the
frozen target. They are recorded in [concurrent_delta.json](../../logs/review/round3/concurrent_delta.json);
this report does not certify an unfinished replacement release. REVIEW changed only this
file and `logs/review/`; scratch installations and generated test outputs stayed outside
the shared source tree. No PR, commit, tag or source fix was made by REVIEW.

## Two reading judgments

**10-minute ISSCC Code-a-Chip reviewer.** The first paragraph answers what this is; the
Japan/open-PDK and author-tapeout context is immediately visible. The real HDL → GDS hero
makes the contribution credible. However, in the actual 1348 × 913 Colab capture, the
first viewport ends after two consecutive descriptions of the same adder: the static-power
message and Run-all action are below it. The reader encounters expanded implementation
code and raw equations before getting to the best circuit explanation. The strongest skim
remains opening → sizing comparison → scaling power → edited-circuit GDS.

**25-minute IC designer.** The divider, fixed-MOS resistor comparison, three-rail cell,
radix identity, matched-device timing zoom and real custom layout form a coherent sequence.
The post-layout figure is particularly effective: a logically unchanged +1 sum glitches
through the opposite rail before its final band entry. The designer will pause at the
unexplained +7.984 mV hand shift versus −12.9 mV SPICE shift, then at differently sized
`adder4` layouts and different `full_add` delays carrying the same names. Label the runs
and explain that one prediction; another limits paragraph would not resolve either issue.

## Round-2 findings 1–5: closure check

| Round-2 finding | Disposition at c84145b |
|---|---|
| 1. Contribution missing from the first screen | **Substantially addressed.** Purpose, checked GDS, Japan, tapeout and hero are present; the power headline exists but remains below the actual Colab first viewport. See finding 3. |
| 2. Static power shown without circuit teaching | **Implemented.** Conducting INV path, independent divider calculation, same-MOS 20/30/45 µm table and 4.17 mW/cell → 0.4 W comparison are present. Rendering and interpretation remain findings 2/4. |
| 3. Repeated representations/process talk | **Mostly addressed in prose and outputs.** Historical drawings/truth tables/full reports move into Details/A/B; `fig_synth` appears once; STA does not become another mandatory chapter. Colab still expands the implementation cells: finding 3. |
| 4. Learning interactions require code edits | **Implemented.** A 90-candidate measured-size slider updates curves, operating point and error/current; a half-adder input selector updates real mapped nets. Saved initial views and exact update states were inspected. The failed Colab run cannot exercise them. |
| 5. No visible editable HDL or resulting GDS | **Implemented and independently reproduced locally.** The literal De Morgan sorter edit produces 4 cells, 384 × 366 µm actual GDS, DRC clean, strict LVS match and all 9 analog states passing. It has a saved schematic/GDS/waveform and a generated takeaway. The tagged Run all still stops earlier. |

The editorial drafts are now integrated as replacements, including captions and A/B. The
remaining work concerns the rendered experience and interpretation, not another rewrite.

## Verification and numerical audit

- Fresh source clone and a separate fresh clone of the pinned PDK,
  **`5d963db9d44e192d37a0489c208bfccf2e2f690c`**; isolated Python 3.12 venv.
- Entire collected suite, split around the STA collection collision described in finding 7:
  **557 passed, 3 failed, 2 skipped**. Core/notebook/submission: 524 passed / 3 failed in
  **697.17 s**; STA: 33 passed / 2 skipped in **0.36 s**. All three failures reach the same
  stale paper-evidence check. STA skips require unpublished integration build artifacts.
  [Test summary](../../logs/review/round3/test_summary.json),
  [commands and wall times](../../logs/review/round3/suite_result.json).
- The broad fresh-dependency run used Python KLayout **0.30.12**, native KLayout **0.30.9**
  and ngspice **46+**. The prescribed system Python/KLayout **0.30.6** independently gives
  the identical paper-hash rejection. The **22 targeted round-1 regressions pass in 12.97 s** (13.08 s wall) with binding 0.30.6;
  recorded in [round1_regression_result.json](../../logs/review/round3/round1_regression_result.json).
  Installed packages are confined to the scratch venv;
  [full dependency snapshot](../../logs/review/round3/requirements_frozen.txt).
- An ordinary **nbclient/Jupyter** run, with a fresh build directory and fresh kernel,
  fails in cell 2 after **1.50 s** of local execution; this excludes installing tools.
  [Result](../../logs/review/round3/nbclient_result.json),
  [failed notebook](../../logs/review/round3/executed_failed.ipynb).
- COLAB independently ran **the exact same c84145b** on a fresh free CPU runtime and hit
  the same exception after successful setup (KLayout 0.30.6/ngspice 42). Its report and
  screenshots were inspected; [archived report](../../logs/review/round3/colab_round3_report.md).
  The earlier **842afe2 / 17 code cells / 384.1 s** success is real and correctly linked
  as historical; it is not evidence that the new 18-cell notebook passes.
- Standalone reproduction of the edited chapter-8 circuit succeeds in **7.27 s**, including
  native DRC/LVS and extracted SPICE. Delays match the saved waveforms: **11.43 / 10.97 ns**.
  [Native probe](../../logs/review/round3/custom_probe.json).
- All **eight embedded paper PNGs** are pixel-identical to their corresponding checked-out
  PNGs. All nine supplied PNGs, the seven saved live PNGs, saved tables and narrative were
  inspected. The native paper records' **nine artifact hashes** match the available native
  artifacts. All six width records and the load record validate against current consumed
  sources and the fresh pinned PDK, with **no compatibility exception needed**. All archived
  four-design members match their hashes.
- Recalculated the displayed context separately from its committed measurement JSON after
  establishing that only SVG hashes fail. This diagnostic does not bypass the notebook
  failure or count as a successful Run all. Recomputed the delay/power fits, checked all
  half/full-adder truth-table rows against integer arithmetic, and reconciled the saved
  DC, fanout, geometry, four-design electrical/physical and producer-time tables.
  [Numerical audit](../../logs/review/round3/numeric_audit.json),
  [saved-table checks](../../logs/review/round3/saved_table_checks.json),
  [figure text](../../logs/review/round3/figure_text.json),
  [image inventory](../../logs/review/round3/images_inventory.json).

| Quantity traced across text/caption/figure/data | Result |
|---|---|
| Paper adder | N=4; **17 top-level lines + shared modules**, 44 NANY + 20 INV = 64 cells; depth 27; 19,683 exhaustive logic states; 1692 × 1590 µm; DRC 0; LVS Match. Live opener is explicitly N=2, 32 cells, 1284 × 1038 µm, 243 logic states. |
| Voltage/conditions | −5/0/+5 V, ±0.5 V acceptance, nominal 27 °C. Paper post-layout/load experiments use 10 fF and 500 ns; the live opening uses 100 fF and 1 µs. These are separate labelled examples. |
| INV middle level | Extracted sweep −0.0395366 V, 0.4071655 mA, 4.0716549 mW; matching schematic DC −0.0395421 V, 4.0716625 mW. Both round as printed. Hand: Ru 11.3272 kΩ, Rd 11.2340 kΩ, −0.0206603 V, 0.443238 mA, 4.43238 mW. |
| Sizing | 90 finite INV points; 17 finite NANY points (the unavailable NANY case stays in evidence). Adopted INV 39.54 mV / 407.2 µA; NANY 44.6 mV / 421.4 µA. Same-MOS RR 20/30/45 µm: **0.06736/39.54/52.44 mV**, **649.0/407.2/260.7 µA**. The signed shift discrepancy is real: finding 4. |
| Cell adaptation/arithmetic | NANY 148 × 115 → 168 × 132 µm, ratio **1.30294 → 1.303**; nine library cells, common height 132 µm; four-cell abutment. HA 5 NANY + 2 INV / 9 states; FA 11 NANY + 5 INV / 27 states. |
| Paper placement | **72.0405 → 48.0705 mm HPWL**, **33.27295%** reduction. Printed 72/48/33 and 72.04/48.07/33.27 are consistent rounding. |
| Full-adder timing/load | 27 states, 500 ns, 10 fF; same-transition sum **100.3353 → 108.6335 ns**, correctly printed 100.3/108.6 or 100/109. Pass/fail bracket **12.8125–12.96875 pF**, correctly printed 12.81–12.97 or ≈12.8. |
| Width scaling | N=1–6; cell counts 16/32/48/64/80/96; device/wire slopes **48.9525 / 56.8814 ns/trit**; **4.1690838 mW/cell**, **400.2322 mW at N=6**; area at N=6 **4.329108 mm²**. Current utilization is 74.0874%, not the old 99% headline. |
| Hand versus SPICE, N=6 | Delay **278.8588 / 299.7129 ns**; all-zero power **400.2482 / 400.2322 mW**. The displayed 400.2/400.2 is four-significant-digit rounding of distinct calculations, not exact equality or a maximum relabelled as a zero-state result. |
| Optional STA figure | **38/39** endpoints within ±20%; mean absolute error **6.78206% → 6.8%**. It is not embedded in the mandatory notebook path. |
| Administrative quantities | Source 33 cells / 18 code; payload 34 cells / 18 executed code, 68 outputs, 8 paper PNGs, 7 live PNGs, 25 HTML tables; **8 files / 5,199,230 bytes**. All package file hashes and source-code identity pass. |

The claims are appropriately scoped: the author **taped out** the reference designs and
has **not measured silicon**; adapted layouts are not described as silicon-proven.
Nominal conditions, tested-state DC maxima, state/transition coverage and final band entry
are distinguished. Appendix A and the wire report explicitly call the area/perimeter
capacitance coefficients **assumed**, including the effective 1/2 µm metal heights and
0.02 fF/µm fringe term. They do not claim calibrated PEX. No additional scope prose is
needed. The different routing runs need identifiers, as finding 5 explains.

## Submission against official requirements

Re-read the live [official rules](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/main/README.md),
[IEEE award page](https://sscs.ieee.org/membership/awards/ieee-sscs-code-a-chip-travel-grant-awards/),
ISSCC27 directory instructions, application guide and FAQ on 2026-10-18. The five repository
source files have the **same SHA-256 values** as `submission/official_sources.json`;
[retrieved-source record](../../logs/review/round3/official_sources_checked.json).

| Requirement | Assessment of `submission/ISSCC27/submitted_notebooks/TritFlow/` |
|---|---|
| Openly licensed Jupyter circuit-design/educational project using open tools/PDK | Satisfied in content: substantive notebook, public source, TR-1um, ngspice/KLayout and Apache-2.0 LICENSE/NOTICE. License files match the root. |
| Communicate idea, decisions, method, results and reproduction | Present, with saved evidence. Reproduction currently fails: finding 1; prediction rendering: finding 2. |
| Folder `ISSCC27/submitted_notebooks/<project_name>/`, project changes confined there | The eight-file folder is prepared correctly. Copy only that directory into the official fork. External runtime source/PDK downloads are described; no repository-wide modifications are required. |
| Team members, references and tool versions | Author/affiliation/email/GitHub appear at the top in the Author control and README; representative is named; sources and actual/pinned tool versions are present. |
| GitHub PR and schedule | Submitter action remains pending. Current deadline is **2026-10-31 11:59 AM Pacific**, not midnight. Monitor the resulting PR. |
| Attendance/poster/travel | Official post-selection obligations are correctly described. The README still exposes an internal confirmation token: finding 6. Membership is encouraged, not required. |

The older application guide's ISSCC26/2025 deadline is superseded by the current event
rules. There is no official numerical file-size limit, ten-minute runtime mandate, mandatory
abstract/pitch or final-layout requirement in the checked rules. The compact saved-output
package is a useful presentation choice. `build_submission.py --check` passes, but checks
payload integrity rather than a fresh execution of its external source release.
[Package audit](../../logs/review/round3/package_audit.json).

## Short summaries of rounds 1–2

**Round 1**, clone `37034be20dc02d8ee82d15170b955b6ef2777d70`: 338 tests passed;
local cold/warm notebook runs completed. Found release/Colab mismatch, falsely accepted
missing VMID, pinned-PDK publication mismatch, unused-input facade, cache-identity gap,
case-distinct SPICE names, flat opening MSB and unreadable expanded drawings.
Round 2 verified the technical corrections with 22 targeted tests and the real 842afe2
Colab pass. [Full round-1 report](../../logs/review/round2/round1_report.md).

**Round 2**, clone `9ca9ba471121a466a602e5a70806e9e6ac5c01b5`: remaining priorities
were the first-screen contribution, divider/sizing teaching, repetitive output/process
text, meaningful controls, and visible edited HDL → custom GDS; routing-title overlap was
minor. The phase-11 rewrite implements that direction. The new release-bundle regression
in finding 1 does not invalidate the earlier Colab result.
[Archived round-2 report](../../logs/review/round3/round2_report.md).

## Final ranked findings

### 1. BLOCKER — the published tag cannot reach chapter 0

**Owner: INTEGRATOR + FRONTEND.**
**Location:** cell 2; `notebook/stages.py:100`, `notebook/paper_evidence.py:25`;
`notebook/assets/paper_evidence.json`.

Both fresh local Jupyter and actual free Colab reject
`figures/out/fig_cell.svg`. **All eight SVG hashes** in the paper record differ from the
committed exports; PNG and numerical-input hashes match. The manifest expects exports
from before the final regeneration. This is a deterministic repository mismatch, independent
of NumPy, solver convergence or cache state. The builder's payload-only check still passes.

**Fix:** publish figures, measurement/presentation identities, source notebook and saved
submission together. Refresh the final export identities after figure generation; preserve
strict checks on scientific inputs. Harmless SVG dates/IDs should not make the design flow
unrunnable. Exercise the *committed tag* in a clean checkout and real Colab before calling
that release runnable. Rebuild the package's release/capture metadata at the same handoff.
Evidence: [eight mismatches](../../logs/review/round3/paper_hash_mismatches.json),
[local traceback](../../logs/review/round3/nbclient.log),
[Colab traceback](../../logs/colab/round3-03-imports-error.png).

### 2. MAJOR — raw equations and overflow break the core teaching sections in Colab

**Owner: FRONTEND; INTEGRATOR owns the paper-figure producer change.**
**Location:** cells 5/7/18/28; `notebook/make_notebook.py:46`, `:55`, `:78`;
`figures/fig_sizing.py:59`.

The actual target renders `\operatorname`, `\frac`, subscripts, `\qquad` and bracket
delimiters literally in chapters 1, 2 and 7. The new Predict-first material therefore reads
like source markup. This was not apparent in a generic HTML export. The sizing figure's
right-hand current-axis label is cut off in the PNG itself; Colab also has horizontal
notebook/table overflow. The other paper plots are readable at notebook width, although
the opening's miniature GDS/code and cell-device labels need full-size access.

**Fix:** emit Colab-supported inline/display dollar math and test the rendered formulas;
break the four gate equations into two short rows. Constrain embedded images and wrap the
Appendix A table inside the notebook width. Shorten both sizing x labels to
`Max |rail I| (mA)`, retaining the over-input-state definition in the caption; resizing a
container cannot recover text already cropped from a PNG. Keep the good gate/current,
cell-row, PNR and band-entry figures. Evidence:
[raw math](../../logs/colab/round3-06-unrendered-math.png),
[sizing capture](../../logs/colab/round3-07-ch2-static-hero.png),
[full-image inspection at 1100 px](../../logs/review/round3/fig_sizing_1100.png).

### 3. MAJOR — the first screen and chapter path still spend attention on repetition/code

**Owner: FRONTEND + EDITOR.**
**Location:** cell 0 and code-cell metadata; `notebook/make_notebook.py:88`–`:107`;
`notebook/learning.py:46`, `:94`.

The title and first two paragraphs now sell the purpose well. But the image footer,
full caption, teaser paragraph and chapter-0 takeaway repeat the same 17-line/64-cell/
DRC-zero/LVS result. In actual Colab, that repetition pushes **4.17 mW/cell → 0.4 W**
and Run all below the first viewport. Setup/imports/opening alone expose **153 code lines**.
More significantly, Colab's chapter-4 capture shows implementation code expanded even
where `metadata.jupyter.source_hidden` is set. The intended folded reading path is not
what this target displays.

**Fix:** use one compact adder-result sentence, put the power/trade-off sentence above the
hero or immediately with that headline, and bring the action up. Fold implementation
cells using Colab-supported presentation metadata; retain the short existing facade
example and visible chapter-8 HDL literal. Verify the folding in actual Colab. As small
control polish, start the half-adder selector at **a=b=+1** to match the preceding figure
and takeaway; its saved default is currently −1/−1. Offer the existing fixed-MOS RR
20/30/45 µm choices directly before the advanced 90-candidate slider.
Evidence: [actual first viewport](../../logs/colab/round3-00-first-screen.png),
[expanded implementation](../../logs/colab/round3-11-ch5-unexecuted.png),
[selector default](../../logs/review/round3/cell14_synthesis_output0.png).

### 4. MAJOR — the sizing prediction gets the sign wrong without explaining the lesson

**Owner: EDITOR + SIM; FRONTEND integrates the comparison.**
**Location:** cell 7; `notebook/narrative/02_sizing.md:36`;
`notebook/predictions.py:29`–`:49`.

For RR 30 → 45 µm at fixed MOS dimensions, the simple divider predicts Y(0) moving
**+7.984 mV**, whereas schematic SPICE moves **−12.902 mV**. Both numbers are correctly
generated. The text simply places them side by side, then changes chapters. A designer
cannot tell whether this is a bug or an intentional demonstration of the model's limits.
It undermines the new prediction → comparison teaching mechanism at its key sizing step.

**Fix:** explicitly state that the approximation predicts the current reduction but misses
the direction of this small voltage change. Explain the omitted bias dependence using the
actual circuit: both F_RR substrate terminals tie to VDD, so their operating biases differ;
the hand routine retains only geometry resistance and constant MOS on-resistance. Explain
or demonstrate those nonlinear terms' contribution rather than implying the two predictions
agree. End with the measured trade-off already available: **407.2 → 260.7 µA**, while
worst error changes **39.54 → 52.44 mV**. Do not change the measured sign or add a generic
qualification paragraph. [Exact calculations](../../logs/review/round3/numeric_audit.json).

### 5. MINOR — different routing runs share names, making correct numbers look inconsistent

**Owner: FRONTEND + EDITOR; INTEGRATOR supplies paper-run identifiers.**
**Location:** cells 0/16/18/32; `notebook/stages.py:424`, `:446`;
`notebook/paper_evidence.py:110`.

The hero and scaling N=4 result use **1692 × 1590 µm**, while Appendix B's `adder4`
is **1740 × 2022 µm**. The paper full-adder sum is **108.6 ns** with wire C, while the
appendix's `full_add` sum is **110.1 ns** at the same stated 10 fF/500 ns conditions.
These are valid different layouts, not arithmetic errors: the paper adder's native record
is **seed 7**, while the four-design archive uses **seed 0**. The appendix tables do not
identify that variant, so a careful reviewer has to infer it from producer code.

**Fix:** add a concise run/seed identifier to the paper captions and appendix table rows,
including the full-adder layout identity. Retain both results if useful; a labelled second
routing realization is sufficient. Preserve the existing explicit paper-N=4/live-N=2
label, which is correct. [Reconciled runs](../../logs/review/round3/numeric_audit.json),
[saved tables](../../logs/review/round3/saved_tables.json).

### 6. MINOR — the otherwise complete package still exposes an internal confirmation token

**Owner: INTEGRATOR / submitter + FRONTEND.**
**Location:** submitted `README.md:16`; `submission/team.json:13`;
submitted `build-info.json` release/capture fields.

The README prints **`[CONFIRM_IN_PERSON_ATTENDANCE_AND_POSTER_IF_SELECTED]`** and its
build metadata consequently reports incomplete team fields, despite a complete author and
named representative. Its recorded release check still names 842afe2/incompatible even
though the public tag resolved to c84145b at review start. The latter is a historical check,
but together these look like an unfinished package.

**Fix:** have the submitter resolve the attendance field truthfully before filing and
regenerate the package; keep internal confirmation prompts out of reviewer-facing text.
Refresh release compatibility/capture fields when publishing the corrected bundle. Preserve
the historical 842afe2 verification record separately from any new exact-source result.
This is a filing cleanup, not a missing eligibility category or demand for another caveat.
[Package audit](../../logs/review/round3/package_audit.json).

### 7. MINOR — default test collection fails before exercising the release checks

**Owner: STA.**
**Location:** `tests/sta/test_timing.py:1`, colliding with `tests/cells/test_timing.py`.

A normal full-suite collection raises pytest's **import file mismatch** for the two
`test_timing` modules. Switching blindly to importlib mode produces missing
`test_propagation` imports in STA's envelope/window tests. REVIEW ran the core suite and
STA separately to complete coverage; this does not make the documented default pytest
collection healthy.

**Fix:** rename the STA timing test module to a unique basename, or consistently package
its tests and sibling imports. Confirm ordinary `python3 -m pytest tests notebook/tests
submission/tests` collects cleanly. Evidence:
[default collection failure](../../logs/review/round3/initial_pytest.log),
[importlib attempt](../../logs/review/round3/pytest.log).
