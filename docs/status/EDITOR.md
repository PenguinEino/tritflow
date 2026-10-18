# EDITOR — phase 4 authoring complete

Updated: 2026-10-19.

## Phase 4 — plan review, reuse and public README

### Done

- Read the new **Plan review 2026-10-19**, binding interfaces, brief, concept,
  author information and current STA/PNR reports. Inspected the actual package,
  flow, schematic, STA, chip, cell-generation and HDL/synthesis entry points.
- Added chapter 7 **Predict with static timing, confirm with SPICE**: directed
  trit-transition midpoint thresholds, side-input classes, propagated slew,
  one endpoint settling tail, ordered events and the matched-set accuracy.
  The one outlier stays visible. The conservative estimate gets one honest
  line about its roughly twofold looseness and finite nominal scope.
- Added `fig_sta.png` as the subsection hero, visually inspected it and added
  its three-sentence paper caption. The caption compares output maxima over
  matched input-transition sets; it does not assert that the two maxima occur
  on one identical transition. The conservative estimate is not the scatter.
- Added chapter 9 **From your HDL to a shuttle-ready top**, with the real
  `layout.result.to_chip()` → `ChipResult.signoff()` calls, MPW frame/passive
  pads, drawing DRC/strict LVS, MDP/mask DRC and MPW precheck. The recorded
  physical checks are separate from `submission_ready=false`. The remaining
  allocation, custom pad map, bonds/supplies/substrate, process/ESD, package/load,
  metadata and organizer-CI steps are explicit. No post-mask LVS is implied.
- Added **Appendix C. Use and extend TritFlow** (`C_reuse.md`): editable pip
  installation from GitHub, native setup, the seven-line API, real module
  CLIs, and concrete cell/operator extension files and checks. New cells need
  evaluator/pin-order/characterization/STA/rendering support in addition to
  geometry; new operators need explicit IR, optimization and mapping behavior.
- Added `readme_final.md`, superseding `readme_draft.md` for publication at
  the source repository root: pitch/figure, Colab and local quickstarts,
  verification scope, optional framed top, Apache-2.0/NOTICE and PDK/original
  design references. The author block exactly matches docs/author.md.
- Updated Appendix A/B, figure placement and the placeholder registry for
  these additions. All new result numbers remain sourced substitutions.
  Kept the earlier interactive specifications optional. No figure was
  regenerated; release alone redraws images before capturing their hashes.

### Decisions recorded

- Use an **editable VCS source install**: setuptools discovers `tritflow*`,
  while the complete flow also requires repository cell/example/notebook
  assets. A plain package-only installation is not a complete-flow quickstart.
- The exactly seven-line example performs one all-zero steady-state smoke
  simulation. The prose says this plainly and points to independent integer
  oracles/transition plans for arithmetic verification. No fabricated coverage
  claim is attached to that short example.
- The STA example takes the actual logical-net `wire_caps` dictionary used
  by SPICE, along with its stimulus/load/ramp. Passing PNR data alone selects
  a different wire estimate. Mapping the native extraction report belongs in
  a collapsed helper, not the visible method code.
- Keep the named successful Colab record historical and source-specific:
  **2c81d2c**, **18 cells**, **405 s**, successful **second** Run all, excluding
  the initial setup attempt and retry gap. It proves neither an uninterrupted
  cold install nor completion of the new phase-4 notebook. The final README
  uses placeholders for those observations and preserves the compatible-badge
  guard separately from the install revision.
- New STA routing labels derive from its own consumed native artifacts.
  Its examples are adder4 seed 7, full_add seed 19, mac1/mul1 seed 0; the
  six scaling adders use seed 7. Do not replace this set with the four-design
  ZIP's all-seed-zero identities.

### Validation

- Editorial checks pass: **123 used tokens**, **161 unique registrations**,
  ten chapter anchors/takeaways, **nine** captions of 1–3 sentences, balanced
  math/details, opening-word limits, exact author block, intact 100-word
  abstract/two-sentence teaser, no trailing whitespace or internal-process
  words in the main chapters. All new Python snippets compile. Main chapters
  are **2,884 whitespace words**, within the reading target;
  Appendix C and README are approximately **810** and **760** words.
- Both API examples are identical and exactly seven lines. Executed their
  source/synthesis prefix in memory: `adder2`, **32 cells**, **243** independent
  integer-arithmetic checks pass; the public schematic API returns valid SVG.
  No physical/extraction/simulation stage was invoked for this prose check.
- Exercised `--help` for synth, PNR, cells, SIM characterization and STA
  characterization. All documented options and private-library paths exist.
- Recomputed STA statistics from all **39** output rows: **38** within
  **±20%**, **6.782062812%** MAPE, **10.4786204 ns** MAE; the exception
  `scaling/adder2/cout` is **+36.4789118%**. The separate bound averages
  **2.1815589945×**; **838** saved output observations (**799** transitions)
  have zero underpredictions. `accuracy_passed=false` and
  `certified_analog_bound=false` remain explicit in the registry/evidence scope.
- Verified all **16** STA code fingerprints, all ten consumed design GDS
  hashes and all ten native post-layout measurement hashes. Their simulated
  maxima still equal the validation's values. **However, 27 of the 622 broad
  source-fingerprint entries no longer match**, including six scaling PNR
  records, their copied input PNR/summary records, and nine results JSON/HTML
  files. The stored `qualified_current=true` is not a live freshness check.
  No current full-source requalification is claimed; the prose labels the
  comparison recorded. Release handling is requested below.
- Inspected the canonical adder chip data: **2500 × 2500 µm**, **23 pads**,
  drawing/mask DRC **0**, strict drawing LVS **Match**, MPW precheck **Pass**,
  `submission_ready=false`, no post-mask LVS stage. All **49** retained
  signoff artifact hashes match. This checks saved evidence, not a fresh
  full-top signoff replay against every current code/input fingerprint.
- Verified the named Colab record's referenced evidence hashes and its retry
  timing scope. The current notebook is a later source; no new Colab claim.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest notebook/tests/test_presentation.py -q -p no:cacheprovider`
  — **5 passed in 0.42 s**. No notebook-generation test was run because it
  writes FRONTEND's .ipynb. There is no `tests/editor/` suite.

### Interface requests / integration

1. **FRONTEND:** insert `C_reuse.md` after Appendix B; render the new ch7/ch9
   sections and `fig_sta` caption/bytes. Populate the **21** new registered
   context fields in placeholders.md and render both appendices' substitutions
   before insertion. Keep accuracy and conservative-estimate columns separate
   and retain all outliers/routing identities in detailed output rows. Supply
   the STA example's logical-net wire-C mapping in its collapsed helper.
2. **FRONTEND/PNR:** preserve a verified portable subset of the canonical
   framed-top reports/pad map/identities. The new chapter must not require the
   author's ignored `build/`. Select the compatible paper adder result for
   the chip demo, not the archived seed-zero adder or an unrelated live layout.
   Use explicit low-level library/PDK/binary options for nondefault settings.
3. **STA/integrator:** before publication, refresh the broad validation
   fingerprint against the updated sources, or retain a verified matching
   historical snapshot for the recorded result. The unchanged GDS/waveforms
   support the quoted saved measurements, but do not waive the changed-input
   guard. Do not silently display the saved `qualified_current` as a fresh
   check. No STA/result paths were changed by EDITOR.
4. **Integrator:** render `readme_final.md` to the public root README only
   with a public immutable install commit and compatible notebook badge.
   Preserve the named Colab record's retry/revision qualification and perform
   a new real-Colab run for the final integrated source. Final figures are
   regenerated only in the release step before image hashes are captured.

No EDITOR authoring remains; these integration/release actions are outside
EDITOR ownership. Wrote only `notebook/narrative/` and this status file. No
package installations, git writes, code/notebook edits, scientific-data writes,
figure regeneration, public README replacement or PR/submission action.

## Phase 3 — REVIEW round 3 findings 3, 4 and 5

### Done

- **Finding 4:** rewrote the closing sizing comparison in `02_sizing.md`.
  It now states that increasing both RR lengths at fixed MOS sizes reduces
  current in the hand model and SPICE, but the model misses the sign of the
  small zero-level shift. The explanation names its geometric RR resistance
  and constant MOS on-resistance, both actual F_RR substrate connections to
  VDD, their different terminal biases and MOS nonlinearity. The chapter ends
  with the measured current-versus-error trade-off, without a generic caveat
  or transition paragraph. All numerical endpoints remain placeholders.
- `predict_first.md` preserves that distinction: the measured current values
  must not be called the hand model's predictions, and the omitted dependencies
  are not presented as a quantitatively isolated attribution to one model term.
- **Finding 5:** added compact run identifiers to the paper flow, PNR,
  full-adder/load and scaling captions. Added an Appendix B routing table
  distinguishing the paper adder, paper full adder, width series and each of
  the four archived designs. Detailed physical/per-output timing tables are
  explicitly specified to repeat the same identifier on every row.
- **Finding 3:** shortened the opening prose and moved the Run-all action into
  it. Removed repeated line-count/cell-count/die/DRC/LVS claims from the
  chapter-0 takeaway and teaser. The teaser now carries the electrical-cost
  lesson and an edit action; the paper-width/live-width distinction remains.
  `figures.md` specifies one compact result sentence, one power sentence,
  the action and hero, with no full caption on the first screen.
- Added exact sources for four sizing endpoint fields and seven routing
  identifiers in `placeholders.md`. No new result constants were typed into
  reader-facing text. No code, notebook, figure, archive or scientific-data
  file was edited.

### Validation

- Rendered the actual comparison from the current INV grid and
  `notebook/predictions.py:divider`: RR **30→45 µm**, predicted zero shift
  **+7.98367 mV**, SPICE **−12.9019 mV**. The measured current changes
  **407.166→260.672 µA**; worst error **39.5421→52.4439 mV**. At the existing
  four-significant-digit display these read 407.2→260.7 µA and
  39.54→52.44 mV. The hand currents themselves are **443.238→271.960 µA**;
  the text claims the correct reduction trend, not exact current agreement.
- Verified MP/MN dimensions remain fixed, RP/RN lengths match, measured
  current agrees with the zero-input DC row, and both resistor substrates
  are VDD in the actual canonical circuit/source SPICE.
- Verified `paper/adder4 · seed 7` against the native PNR hash in the saved
  paper evidence; GDS begins **c8b426ff5408**. The N=4 scaling GDS matches
  that same artifact; all displayed widths use seed 7.
- Verified `paper/full_add · seed 19` through the native summary's consumed
  PNR digest and the saved paper-summary hash; GDS begins **3f51bddf7aaa**.
  The load sweep consumes the identical full-adder GDS/PNR hashes.
- Verified the archived adder4/full_add/mac1/mul1 PNR members against their
  ZIP manifest hashes; all use **seed 0**. Rendered the new routing-identity
  table successfully with those source-derived values. Equal paper/archive
  full-adder die dimensions do not imply the same routing realization.
- Editorial checks pass: **102 used tokens**, **140 unique registrations**,
  ten chapter anchors/boxes, eight captions of 1–3 sentences, intact 100-word
  abstract and two-sentence teaser, no literal sizing-result numbers or
  internal-process words in chapters, balanced math/details and no trailing
  whitespace. Main chapters are **2,326 whitespace words**; the intro is
  **82 words**. The opening no longer repeats the numerical adder-result fields.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest notebook/tests/test_presentation.py -q -p no:cacheprovider`
  — **5 passed in 0.45 s**. No notebook-generation test or end-to-end run was
  invoked; those would write FRONTEND's notebook and need the context additions
  below. This handoff does not claim a new Colab rendering verification.

### Interface requests / integration

FRONTEND can integrate without changing the measured signs or repeating the
adder result:

1. Populate four new context values from the same adopted/longer-RR INV rows:
   `sizing.adopted_rr_um`, `sizing.selected_rr_um`,
   `sizing.selected_current_ua`, `sizing.selected_error_mv`.
2. Populate `paper_adder.run_id`, `paper_post.run_id`,
   `paper_scaling.run_id`, and `archive.{adder,full_add,mac1,mul1}_run_id`.
   Exact formulas, source paths and hashes are in placeholders.md. Preserve
   verified native paper seeds/GDS identities in the portable paper evidence;
   runtime must not reach into ignored `build/`. The existing paper subsets
   do not yet retain their seeds. Archive PNR members already do.
3. Render the newly added Appendix B routing table before inserting it. The
   inspected generator removes the old summary table but inserts the remaining
   appendix text without general token substitution. Add **Routing realization**
   to generated physical and per-output timing rows, retaining separate paper
   and archive identities even when die dimensions match.
4. Keep one generated adder-result sentence and one power/trade-off sentence
   immediately before the hero, with the action visible. Use the new teaser
   or its equivalent generated power line once. Keep the run identifier in
   the compact headline when omitting the full paper caption. Colab code-folding
   and selector-default fixes remain FRONTEND work, not EDITOR edits.

No EDITOR authoring work remains. The changes are confined to
`notebook/narrative/` and this status file. No packages installed, git writes,
figure regeneration, data mutation, public README write or PR submission.

## Phase 2 — done

- Read all eight paper-figure scripts and visually inspected every PNG in
  `figures/out/`. No figure script/image was edited or regenerated.
- Realigned chapters to the existing static heroes: fig_flow → 0/teaser,
  fig_gates → 1, fig_sizing → 2, fig_cell → 3, fig_synth → 4/5 (reuse panels,
  no duplicate required), fig_pnr → 6, fig_postlayout + fig_scaling → 7.
  Chapter 8 retains the actual edited-design output; chapter 9 uses a static
  measurement table. No unrelated adder image represents a custom circuit.
- `figures.md` now leads with the static placement map and image/caption
  consistency requirements. All earlier interactive specifications are retained
  under an explicit optional-later section. Main prose no longer promises
  unimplemented controls. Chapter 8's actual HDL editing remains part of the flow.
- Tightened every affected What-this-shows box to its figure's quantities.
  Fixed four-trit paper contexts are separate from the live two-trit example.
  HPWL is identified separately from routed wire length; DC power is the
  maximum over documented states; the timing endpoint includes carry/MSB sum.
- Added `notebook/narrative/captions.md`: eight paper-style captions, each
  with 1–3 sentences and numerical substitutions sourced in placeholders.md.
- Added `readme_draft.md` for the public repository root and
  `pr_description.md` for the official Code-a-Chip PR. Both reproduce the
  author block in docs/author.md exactly. No phone, membership, attendance,
  submission approval or actual PR action is inferred. README links are
  written for their intended root destination, not the narrative directory.
- Retained all prediction derivations. The static sizing comparison now chooses
  the longest common resistor length at adopted MOS dimensions, so no selector
  is required to identify its comparison. Appendix B now has a sizing
  unavailable-results row.

### Figure corrections for the owner before publication

The prose/captions are complete; the following images/scripts remain outside
EDITOR ownership and require their owner's update to match the final data:

1. **fig_sizing:** the current grid has 18 NANY candidates but only **17 finite
   plotted results**. The unavailable case rejects a nonphysical DC solver root.
   The PNG/script title “18 sizes, all pass” is therefore incorrect. The new
   caption counts finite points and Appendix B retains the missing case. Its
   scatter x source is `max_static_current_a` over logical states, so “Static
   current at the 0 level” is also too specific as a general axis definition.
2. **fig_postlayout:** current native summaries explicitly compare identical
   extracted devices without/with wire C; the old “schematic” baseline labels
   must be replaced. The current paired sum-zoom numbers resolve to
   **100.3353/108.6335 ns** on the selected post-wire-slowest sum step. Regenerate
   the zoom, legend and annotations from the same native inputs as the caption.
3. **fig_scaling:** the inspected PNG shows **49.2/47.3 ns/trit** and calls its
   baseline schematic. The current complete corrected source gives
   **48.9525/57.0342 ns/trit** for identical extracted devices ± wire C.
   Regenerate the points/fits and baseline labels, identify the measured
   carry/MSB-sum endpoint, and label static power “maximum over tested states.”

These values are observations for the handoff, not frozen reader text. All
caption numbers remain placeholders. `FIG_REF` affects only the scripts' reads
through figures/data.py, not all native build/cell inputs; retain a consistent
snapshot when regenerating. No automatic claim that an existing PNG matches
today's JSON is made.

FRONTEND/integrator should embed or rebase narrative image links in the notebook
and include them in its static payload. Publish the new README/PR substitutions
only against a matching release/source/capture. The current old payload has an
incompatible launch tag and `colab_verified=false`; the drafts use truthful
unavailable text until replaced by matching evidence. The PR draft expects
LICENSE and NOTICE in the final project folder; confirm the final package
contains both (the inspected legacy seven-file payload did not contain NOTICE).

### Phase 2 validation

- Ten chapter anchors/boxes; primary-image links; ≤80-word chapter openings
  and ≤150-word intro; balanced math/details; no internal-process words in
  chapters; no trailing whitespace — pass.
- All **93 currently used substitutions** are covered by **129 unique
  registrations**. The other registrations are retained for optional views.
- Eight captions of 1–3 sentences, no copied numerical results; exact author
  block in both public drafts; original 100-word abstract and two-sentence
  teaser preserved — pass. Main chapter prose is **2,336 whitespace words**,
  about **15.6 minutes at 150 words/minute** before figure study.
- Independently resolved all new source paths/formulas. Fixed-adder counts
  are NANY=44/INV=20, die 1692×1590 µm, HPWL 72.0405→48.0705 mm
  (33.27295% reduction). NANY reference/adapted area ratio resolves to 1.30294.
  Both illustrated arithmetic input vectors match actual mapped simulation.
- Ran the exact public DC sweep used for the plotted INV zero-input point:
  −0.0395366 V, |I(VDD)|=0.407165 mA, signed rail power 4.07165 mW.
  This is the extracted-cell source, distinct from the source-level sizing
  comparison in the earlier hand estimate.
- Current width/load source fields resolve, including same-transition timing,
  all 27 full-adder states and the 12.8125–12.96875 pF measured load bracket.
  This is an editorial source audit, not a new PNR/all-width qualification.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest notebook/tests/test_presentation.py -q -p no:cacheprovider`
  — **1 passed in 0.31 s**. No notebook generator or .ipynb write was run.

Only `notebook/narrative/` and this status file were written. No packages,
git writes, commits, public README changes or PR submission. There are now
21 narrative files. No EDITOR authoring work remains.

## Phase 1 record

## Done

- Read AGENTS.md, concept, binding interfaces/editorial plan, EDITOR brief,
  current notebook source and its output inventory, and every stream's status.
- Read accepted ISSCC25 MARTIn and VLSI26 Wrøngm notebooks for presentation
  structure; checked ISSCC26's accepted-project list (no accepted .ipynb paths
  were present in that period's accepted folder in the public tree).
- Checked actual JSON schemas and public flow/simulation APIs for numerical
  substitutions. The current notebook has no saved outputs; historical executed
  outputs and the COLAB/REVIEW reports are evidence about their own revisions.
- Delivered all ten chapter files, Appendix A/B, two-sentence teaser, title
  options, three-sentence pitch and exactly 100-word abstract.
- Delivered concrete hero/control/static-fallback specifications for every
  chapter and appendix in `notebook/narrative/figures.md`.
- Delivered two/three-line chapter predictions and the detailed variable,
  model-parameter, units and source derivations in `predict_first.md`.
- Registered all **92** unique reader-facing placeholders in `placeholders.md`,
  with actual JSON fields/public API calls, transformations and missing/failure
  behavior. Main chapter text is **2,252 whitespace words**, about **15 minutes
  at 150 words/minute**, leaving figure time within the editorial reading target.
- Generated the four original GDS bounding-box areas into the small portable
  `reference_geometry.json`, with source SHA-256 and measurement method. All
  four hashes agree with the independent equivalence report. No reference GDS
  was modified; the snapshot avoids a Colab dependency on the author's checkout.

## In progress

None in EDITOR ownership. FRONTEND integrates text, predictions and controls;
the ongoing qualification/release work supplies final numerical substitutions.

## Decisions

- Numerical results resolve from validated current records; historical status
  tables are never the source of a notebook result. Pinned-PDK republishing is
  ongoing. Partial scaling results must retain failed/running widths visibly.
- The wiring experiment uses identical extracted devices with/without wire C.
  The old schematic-versus-extracted fit is unsuitable for that comparison.
- Main text will explain static power and report actual solved rail-current
  utilization, without repeating the old near-limit headline after power feeds
  have changed. Interpretations must follow current measurements.
- Chapter 0 counts top-level HDL lines and explicitly credits shared arithmetic
  modules; it will not imply those modules are contained in the displayed file.
- Hand estimates use a first-order INV divider and the pinned resistor model's
  correct width branch. Power uses signed rail powers, not the sum of absolute
  rail currents. Carry predictions use only a single slice as calibration.
- Figures and prose are deliverables; FRONTEND owns all plotting/notebook code.
- Structural constants (chapter numbers, trit equations, radix weights, syntax,
  unit conversions and product names) remain literal. Experimental values and
  context dates resolve through the registry. This interprets “numbers are never
  typed” as prohibiting copied result numbers, while preserving readable math.
- Chapter 1 starts at INV's middle input so the prediction precedes the measured
  comparison; NANY remains selectable. The top-level intro is below 150 words,
  other chapter openings below 80 words. Detailed limits occur only in Appendix A.
- Support cells have no fabricated taped-out area/timing counterpart. The main
  comparison caption applies to INV/NAND/NOR/NANY; BUF and ties/FILL get a
  scope-appropriate dimensions/qualification caption instead.
- Prediction/source checks confirm the simple baseline INV estimate is
  −0.0206603 V and 4.43238 mW versus source-level DC −0.0395421 V and
  4.07166 mW at the adopted bias. These are authoring validation observations,
  not frozen notebook constants. The model uses the special W=2.8 µm RR
  polynomial, nominal U0/TOX/VTH0, and stated SiO2-permittivity assumption.

## Blockers

None for EDITOR deliverables. Final measured substitutions and clean-Colab runtime depend
on the existing qualification/release work; no successful Colab claim is made.

## Interface requests

FRONTEND:

1. Insert `00_intro.md` … `09_next.md`, `A_limits.md`, `B_evidence.md` at
   their chapter/figure anchors. `teaser.md` is the caption at the top;
   `figures.md`, `placeholders.md`, `predict_first.md` are implementation notes,
   not extra reader chapters. Preserve existing author/license metadata.
2. Use exact-token substitution; whole-file `str.format` would damage LaTeX
   braces. Missing/stale/failed/running states replace the entire success box.
3. Width selection needs matching native GDS/PNR/waveforms, not just scaling
   summary JSON. Package verified native views for every offered width, or
   explicitly limit available views while retaining failed/running widths in
   the overview. The current four-design archive is a different experiment.
4. The zero-state power comparison needs each scaling run's hashed
   `postlayout/static.json` or a verified compact export. The summary contains
   maxima/means, not a named zero-state value. If absent, omit that measured
   comparison sentence rather than relabel the maximum. The independent cell
   sum is already fully specified and checked.
5. Bundle the small generated `reference_geometry.json` when retaining area
   ratios. Verify it against current equivalence source hashes before display.
6. Preserve actual fresh/recorded distinctions in Appendix B. The old real-Colab
   failure/manual-follow-up elapsed time is not a successful runtime benchmark.

No shared Python/JSON interface modification is requested. Optional STA,
corner or chip-wrapper results have no required unconditional claim.

## Validation

All authoring checks passed:

- Ten chapter anchors and What-this-shows boxes; introduction/opening word
  limits; balanced display math/details; no internal process words in chapters;
  no trailing whitespace; every one of the 92 substitutions registered once.
- Exactly 100 abstract words, three pitch sentences and two teaser sentences.
- Four portable reference-GDS hashes/areas match independent evidence.
- All 90 INV sizing candidates admit positive branch resistances/overdrives
  in the specified hand model; source-level baseline dimensions match the grid.
- Actual public synthesis reports give HA = NANY×5 + INV×2 and
  FA = NANY×11 + INV×5. All 9/27 states pass independent integer arithmetic
  in both source and mapped simulation.
- The two-trit all-zero ideal network contains only zero-valued internal nets;
  its signed cell-DC sum resolves to 133.416 mW with the inspected char files.
  Single-slice carry-prediction paths resolve in the current scaling schema;
  this field check is not an all-width requalification claim.
- `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest notebook/tests/test_presentation.py -q -p no:cacheprovider`
  — **1 passed in 0.13 s**. This checks the display formatting used by the
  narrative. No new implementation-mirroring unit tests were added.

There is no `tests/editor/` suite. Do not run the notebook document-generation
test for this text-only handoff: it writes the .ipynb owned and concurrently
edited by FRONTEND. No physical/analog rerun is necessary for a prose change.

Repeat the central editorial checks from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
from pathlib import Path
import json, re
p = Path('notebook/narrative')
chapters = sorted(p.glob('[0-9][0-9]_*.md'))
assert len(chapters) == 10
reader = chapters + [p/n for n in ('A_limits.md', 'B_evidence.md', 'C_reuse.md', 'pitch.md',
                                  'teaser.md', 'captions.md', 'readme_draft.md',
                                  'readme_final.md', 'pr_description.md')]
pattern = r'\{([a-z][a-z_]*\.[a-z][a-z_0-9]*)\}'
used = set().union(*(set(re.findall(pattern, f.read_text())) for f in reader))
registered = re.findall(r'^\| `\{([a-z][a-z_]*\.[a-z][a-z_0-9]*)\}` \|',
                        (p/'placeholders.md').read_text(), re.M)
assert used <= set(registered) and len(registered) == len(set(registered))
for f in chapters:
    s = f.read_text()
    assert 'What this shows' in s and re.search(r'<!-- figure: ch\d -->', s)
    assert not re.search(r'\b(?:TODO|fingerprint|producer|campaign|stream|integrator|content-keyed)\b', s, re.I)
    if f.name == '00_intro.md':
        assert len(s.split('## 0.')[0].split()) <= 150
    else:
        assert len(s.split('\n\n', 2)[1].split()) <= 80
for f in reader:
    s = f.read_text()
    assert s.count(r'\[') == s.count(r'\]')
    assert s.count('<details>') == s.count('</details>')
    assert not re.search(r'[ \t]+$', s, re.M)
pitch = (p/'pitch.md').read_text()
abstract = pitch.split('# Abstract — 100 words\n\n')[1].split('\n# Why')[0]
assert len(abstract.split()) == 100
assert len(re.findall(r'\.(?:\s|$)', (p/'teaser.md').read_text())) == 2
three = pitch.split('# Three-sentence pitch\n\n')[1].split('\n# Abstract')[0]
assert len(re.findall(r'\.(?:\s|$)', three)) == 3
reference = json.loads((p/'reference_geometry.json').read_text())
eq = json.loads(Path('cells/out/equivalence_report.json').read_text())
for cell, row in reference['cells'].items():
    assert row['source_sha256'] == eq['schematic_equivalence'][cell]['original_gds_sha256']
print('Narrative checks passed:', len(used), 'registered placeholders')
PY
```

Tone references inspected:

- [ISSCC25 MARTIn notebook](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/main/ISSCC25/accepted_notebooks/MARTIn/main_notebook.ipynb)
  — purpose → algorithms → physical implementation → verification/results.
- [VLSI26 Wrøngm notebook](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/main/VLSI26/accepted_notebooks/Wr%C3%B8ngm/Wr%C3%B8ngm.ipynb)
  — device insight and hand-analysis connection before simulation/design controls.
- [ISSCC26 accepted list](https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io/blob/main/ISSCC26/README.md)
  — reviewed for scope; no claim that an unavailable accepted notebook was read.

No packages installed; no git write commands; no code, notebook generator,
.ipynb or foreign owned paths changed. Eighteen files were delivered in phase 1 under
`notebook/narrative/` plus this status file.
