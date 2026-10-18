# REVIEW — round 2, reader and editorial review

**Integrate the narrative drafts and paper figures. They materially improve the notebook.**
The working flow is convincing; the current reading path still hides its two reasons to
remember it. This round finds five major reader-facing issues and one minor figure-layout
issue. It does not reopen the completed Colab or round-1 engineering qualification.

Read `docs/editorial.md` first and treated its purpose, two memorable points, chapter
structure and reading budget as binding. Reviewed as a ten-minute ISSCC Code-a-Chip skim
and a 25-minute IC-design read. These are editorial judgments, not a measured reader study.

Snapshot: **`9ca9ba471121a466a602e5a70806e9e6ac5c01b5`**, cloned read-only for targeted
checks at `/tmp/tritflow-review2-0pq0qhoz/source`. Release **`colab-v0 = 842afe27bead953c9ffd48a7ddceadb57fe0d39d`**
passed real free-Colab Run all in **384.1 s including setup**, all **17 code cells**.
The retained COLAB report/screenshots and `notebook/colab_verified.json` support that result.
I did not repeat Run all. All nine `figures/out/*.png`, the chapter drafts, captions,
prediction instructions and relevant Colab screenshots were inspected.

Other streams changed files during review. The final observed HEAD was
`b0319024f2d16fc28f0633880b687b24e51e4430` (STA phase 4), after `638bb02`,
with pending notebook/package edits.
The live generator now shortens the introduction, prints the verified Colab time and adds
Appendix B. SIM's `a6a81c1` repairs the load-plot axis. Those improvements are credited
below; the original stale release warning and trillion-pF axis are **not** new open findings.
Evidence: [snapshot/context](../../logs/review/round2/context.json),
[live delta](../../logs/review/round2/live_delta.json),
[figure inventory](../../logs/review/round2/figures_inspected.json).

## The two reader judgments

**Ten-minute skim:** the title says HDL to GDS, but the first screen does not tell me why
this particular flow matters. Japan's open 1 µm PDK, the author's taped-out starting cells,
the actual clean layout and the static-power cost are not presented together. At the
reviewed commit the introduction is 439 words, largely author/setup/reuse instructions;
the live shortened version is 164 words including metadata, but still has no teaser image,
Japan/tapeout context or power takeaway. I would skim to the figures. Until the scaling
plot, I could mistake this for another general HDL tutorial with unusually extensive checks.

**25-minute IC-design read:** I can trace the implementation and trust the checks. I cannot
easily tell what I am meant to predict, vary or conclude. Chapter 2 describes the
characterization machinery before explaining the divider. Chapters 4/5 repeat the same
arithmetic at several representations. Chapter 7 mixes the electrical result with long
instructions about records and solver initialization. The engineering detail is useful,
but its placement makes the central circuit insight an inference the reader must make.

The main reading path should be **working layout → why the middle level draws current →
sizing choice → arithmetic/mapping → wiring effect and width/power trend → my edited GDS**.

## Ranked findings

### 1. MAJOR — the first screen does not sell the specific contribution

**Location:** notebook cell 0 and chapter-0 cells 3/4;
`notebook/narrative/00_intro.md:3`, `:20`, `:29`;
`notebook/narrative/teaser.md:1`. **Owner: EDITOR + FRONTEND; integrator for author placement.**

The shortened live introduction fixes the obsolete Colab warning, but still leads with the
full author block and a generic build/inspect pitch. The reader has to discover the
Japan/PDK/tapeout context elsewhere. There is no result image above setup and no second
memorable point on the opening screen. The narrative draft supplies the missing context
and actual flow image, so it is a substantial improvement, but its first paragraph still
says “DRC/LVS results” rather than stating the successful outcome. Its power insight starts
only in chapter 1.

**Concrete fix:** title, a short purpose/context paragraph, `fig_flow`, two generated
result sentences, then the Colab action. Preserve the exact author information in an
Author block in the title cell after the pitch; do not let it occupy the whole opening.
The two sentences should say, in substance:

- A short ternary HDL adder becomes a DRC-clean, LVS-matched GDS on Japan's NDA-free
  OpenSUSI TR-1um, using a library adapted from the author's 2026 taped-out circuits.
- The middle level has a measurable cost: about 4.17 mW per mapped cell for this adder
  mix and about 0.40 W at six trits; sizing changes current and voltage accuracy.

Use the actual displayed top-level HDL count, **17 lines plus shared modules**, rather
than forcing the storyboard's illustrative “30 lines.” Keep the successful **384.1 s**
Colab result beside the launch action. Display the four-trit paper example once and label
it as such; the live example is two trits. This makes both the purpose and the educational
question visible before any Python setup.

### 2. MAJOR — the static-power insight is shown as data, not taught as a circuit

**Location:** notebook cells 6–11 and 27;
`notebook/narrative/01_gates.md:18`, `02_sizing.md:29`, `07_results.md:17`;
`figures/out/fig_gates.png`, `fig_sizing.png`, `fig_scaling.png`.
**Owner: EDITOR + FRONTEND, using existing SIM results.**

The notebook goes from gate equations to characterization/fanout tables and scatter plots.
There is no “Predict first” divider calculation or generated “What this shows” takeaway.
A knowledgeable reader can infer I ≈ 0.4 mA and P ≈ 4 mW, but is never led through the
simultaneously conducting upper/lower branches. Chapter 2's first result is about how data
was qualified. Even the draft sizing takeaway counts finite candidates and lists the
adopted point; it does not compare two sizes to demonstrate the trade-off.

**Concrete fix:** integrate the drafts' chapter-1 divider and chapter-7 cell-power sum.
Show the conducting INV path beside I = ΔV/(Ru+Rd) and P = ΔV·I, then reveal the existing
hand/SPICE comparison specified in `predict_first.md`. In chapter 2, retain the same MOS
sizes and compare actual RR candidates rather than opening with candidate counts:

| RR length | Worst level error | Maximum static rail current |
|---|---:|---:|
| 20 µm | 0.0674 mV | 649 µA |
| 30 µm, adopted | 39.5 mV | 407 µA |
| 45 µm | 52.4 mV | 261 µA |

These numbers were checked directly in the current INV grid. They give a concrete
accuracy/current trade-off without a new experiment. Generate them at integration time.
Put the **4.17 mW/cell / 400 mW at N=6** sentence immediately above the scaling power
panel. Use current power-network utilization if mentioned; the present N=6 value is
**74.1%**, so do not revive the old 99%-near-limit headline. This is a result update,
not a request for another qualification paragraph. Evidence:
[data checks](../../logs/review/round2/data_checks.json).

### 3. MAJOR — repeated representations and process paragraphs break the 25-minute path

**Location:** notebook cells 8/10, 13, 15/17/19, 22/24/26;
`notebook/narrative/03_cells.md`, `05_synthesis.md`, `07_results.md`, `A_limits.md`, `B_evidence.md`.
**Owner: FRONTEND + EDITOR.**

The reviewed notebook has 2,204 prose words and 578 code lines. Word count alone fits the
budget; the number of full output views and interruptions does not. In chapters 4/5 the
reader gets historical HA/FA schematics, two truth tables, two gate graphs, a two-trit
hierarchical schematic and another flat half-adder. Chapter 3 shows cell geometry, another
device-map geometry, its full device table and an abutted row before returning to arithmetic.
Chapter 7 has **600 words across cells 22/24/26**, largely measurement/record/source/solver
explanation, before the width/load result. Examples of process text to relocate are
“Every member hash, consumed abstract, manifest/publication identity...” and the full
`run_scaling` / `sweep_output_load` signatures.

**Concrete fix:** integrate the chapter drafts and A/B; change the display order as well
as the Markdown. Keep one main view for each question:

- Chapter 2: divider prediction and sizing hero first; full AC-C/fanout tables in Details/B.
- Chapter 3: `fig_cell` plus one selected device-map view; full mapping table/alternate
  geometry/qualification tables collapsed.
- Chapter 4: radix equality + `fig_synth`; full truth tables collapsed, with the generated
  exhaustive count left visible.
- Chapter 5: reuse that figure's graph, show one mapping transformation and a selectable
  value-colored schematic. Remove the consecutive uncolored/colored full-graph duplicates
  from the main path.
- Chapter 7: one band-entry zoom → sizing/load consequence → width/static-power result.
  Put archive policy, resistor-terminal orientation, Newton initialization and producer
  APIs in A/B. Keep running checks exactly as they are.

The late Appendix B is a good start, but the main-chapter paragraphs above remain. Replace
those paragraphs instead of appending the new drafts beneath them. The drafts' decision
not to repeat `fig_synth` at full size is correct.

### 4. MAJOR — the required learning interaction is still a code edit

**Location:** notebook cell 11 (`SIZING_INDEX`), cells 17/19 (fixed input dictionaries);
`notebook/narrative/figures.md:3`–`:7`; `docs/editorial.md:46` and storyboard.
**Owner: FRONTEND; EDITOR aligns the handoff with the binding plan.**

Layer/device selectors, physical-net dropdowns and placement playback exist and are useful.
The two explanatory experiments do not: changing a sizing candidate or a gate's input
requires editing a Python variable/dictionary and rerunning a cell. The phase-2 narrative
handoff makes all scientific sliders optional. Integrating those static drafts alone would
therefore leave the plan's “change it and watch what happens” teaching mechanism unfinished.

**Concrete fix:** keep the excellent static heroes and add one small lookup control in
chapter 2: RR length or a few named W/L candidates at fixed other dimensions. Update the
transfer curve, operating point, error/current readout and adopted marker from the existing
grid; show the hand prediction before the SPICE value. A second compact input-vector
selector can recolor the existing mapped half-adder. Both can use precomputed Plotly
states with an initial static view. No new simulation campaign or large widget framework
is needed. Prioritize the sizing control over additional routing/STA features.

### 5. MAJOR — “your circuit” does not make the edit or its new layout visible

**Location:** notebook cell 30; `notebook/narrative/08_your_circuit.md:11`–`:23`.
**Owner: FRONTEND + EDITOR.**

The code reads `source = example.path.read_text()  # edit this string`, then displays that
source inside an evidence block. There is no visible HDL literal to edit. The chapter
ends in a colored gate graph, a physical-statistics Details block and a waveform; it does
not display the generated custom GDS. The notebook's opening promise is HDL to GDS, so
this is exactly where a reviewer should see that the editable flow belongs to them.

**Concrete fix:** expose the chosen HDL in a separate, short editable code cell, with the
run cell below it. Give one successful first action (select `sign`, or replace the sorter's
minimum with the equivalent `~((~a)|(~b))`) before the optional deliberately failing edit.
Show the **actual custom-result GDS** beside the custom waveform and a compact
DRC/LVS/oracle outcome. The narrative draft gives this chapter the right purpose, but
integration must implement the visible source and output; inserting its prose alone will
not do so. Reuse the existing render/flow APIs.

### 6. MINOR — routing and placement controls cover titles

**Location:** `tritflow/viz/layout.py:159`, `:233`, `:244`, `:283`;
Colab screenshots `round2-03-ch00-routing.png`, `round2-11-ch06-placement.png`,
`round2-15b-ch07-load-boundary.png`. **Owner: PNR; SIM's separate axis correction is complete.**

The physical-net selector and Play/Pause row overlap the routing/placement titles in the
actual Colab captures. Give those views a clear title and a separate control row.
The release also had a load plot spanning up to **1T pF**, compressing 0.01–30 pF data;
that separate issue is now fixed and is not an open finding against the latest head.

**Concrete fix:** PNR gives the title and controls distinct rows with reserved top margin
at normal Colab width. SIM's `a6a81c1` already fixes the load issue after the reviewed
release: I checked a log-axis range of **[-2, 1.4771]**, corresponding to **0.01–30 pF**,
and the boundary caption uses paper coordinates. Carry that existing correction into
the integrated artifact; no new load study is requested. The static `fig_postlayout`
already presents the bracket clearly. Evidence:
[axis check](../../logs/review/round2/load_axis_fix.json).

## What to integrate from narrative/ and figures/out/

**Yes: integrate chapters 00–09, the eight captions and Appendices A/B as replacements.**
Their titles, divider explanation, explicit arithmetic identity, two/three-line predictions
and generated takeaway boxes fit Code-a-Chip much better than the current audit-log prose.
`predict_first.md`, `placeholders.md` and the long control specifications are implementation
notes, not additional reader chapters. Preserve the short numerical comparison in the
chapter and keep parameter parsing/source details outside it.

Three draft adjustments before insertion:

1. Move both memorable points into the first screen and make chapter 2's takeaway a
   comparison of sizes, as findings 1/2 specify.
2. Keep the existing live views where they teach something; a static reading path and a
   sizing/input selector complement each other. Making every interaction optional does not
   satisfy the binding plan.
3. Refresh stale handoff notes: `figures.md:42` still mentions “18 sizes, all pass” although
   the inspected PNG says **17 solved sizes**; the “rename device-only” requests are already
   reflected in the supplied PNGs. `placeholders.md:394` describes an old unsuccessful
   payload. Substitute the verified 842afe2/384.1 s result instead of copying obsolete
   unavailable/run-failure text into the rewrite.

| Inspected PNG | Reader judgment and placement |
|---|---|
| `fig_flow` | Strong opener. Five equal-width panels make the actual GDS only about 150–170 px wide at a 1000 px notebook width. Enlarge the GDS/check outcome, or use two rows; keep code/count detail subordinate. Put the clean/LVS result in a visible caption, not only small bottom text. |
| `fig_gates` | Strong chapter-1 hero: voltage directly above current makes the physical cost visible. Start at INV's zero input and show the highlighted current path in the accompanying schematic; then compare the other gates. |
| `fig_sizing` | Essential chapter-2 hero. Pair with the same-MOS 20/30/45 µm comparison. Keep its caption explaining hollow points and triangles; the script creates a marker key but does not draw that key in the image. |
| `fig_cell` | Clear original/adapted comparison, device groups and three continuous rails. Integrate as the static overview; the live device map can supply detail without four expanded views. |
| `fig_synth` | Useful combination of source, colored half-adder and full-adder hierarchy. Use once across chapters 4/5. The small source text belongs in a selectable code block as well as the image. |
| `fig_pnr` | Clear before/after and **72 → 48 mm HPWL** message. Better main-path summary than requiring animation playback; leave animation available underneath. |
| `fig_postlayout` | The best electrical teaching figure. Emphasize panel b: the sum remains logically +1 but glitches through the opposite rail, so final band-entry time matters. Then show **100 → 109 ns** with wire C and the load boundary. Put the all-27-state sequence below the zoom if reading space is tight. |
| `fig_scaling` | Essential: **4.17 mW/cell, about 400 mW at N=6**, plus carry slope and area, are immediately readable. Give the power panel a one-sentence conclusion before the figure. This closes the chapter-1/2 circuit explanation. |
| `fig_sta` | Readable parity figure, but a third timing-analysis thread is unnecessary for the two main messages. Put it in an optional appendix/detail after the required story, rather than adding another mandatory chapter-7 result. |

These are good opaque, high-resolution static figures. Use their supplied captions, embed
images in the distributed notebook and retain full-size access. They should replace
redundant main outputs, not add nine more full outputs to the existing stack. Keep the
paper N=4/live N=2 distinction in a short label so the area/count tables do not look inconsistent.
**Owners:** integrator coordinates changes to paper-figure producers in `figures/`;
EDITOR owns caption/narrative changes; FRONTEND owns notebook embedding and display order.

## Suggested reading path and chapter budget

| Group | Keep in the main path | Budget |
|---|---|---:|
| Intro / 0 | Purpose, Japan/tapeout context, two results, one flow hero, Run all action | 2 min |
| 1 / 2 | Divider → hand power estimate → SPICE → one sizing change | 6 min |
| 3 | Original/adapted cell and continuous three-rail row | 2 min |
| 4 / 5 | One radix example, shared adder hierarchy, one mapping/input change | 4 min |
| 6 | Before/after layout and HPWL; optional playback | 3 min |
| 7 | Same-output glitch/band entry, load boundary, width/power consequence | 5 min |
| 8 / 9 | Successful edit/new GDS and January 2027 measurement plan | 3 min |

This is a proposed **25-minute** budget, not a benchmark. A ten-minute skim should work by
reading the opener, sizing comparison, scaling conclusion and edited-circuit result;
no cache/source-policy paragraph should be required to understand those four stops.

## Short round-1 closure

Original review: `37034be20dc02d8ee82d15170b955b6ef2777d70`, 338 tests passed and local
cold/warm execution. Full report preserved at
[round1_report.md](../../logs/review/round2/round1_report.md).

| Round-1 issue | Round-2 disposition |
|---|---|
| Old release / no successful Colab run | **Fixed:** matching 842afe2 tag, all 17 cells, 384.1 s. The live introduction now reports it. |
| Missing VMID rail accepted | **Fixed:** real drawn-rail proof; metal deletion, label deletion and severed-rail regressions pass. |
| Pinned-PDK width/load mismatch | **Fixed:** all six width records and load record validate against the pinned PDK; the exact display-only schematic-delegate compatibility is tested separately. |
| Facade rejects unused input | **Fixed:** full facade includes physical isolated-pad proof; deleting its label invalidates extraction. |
| Abstract/manifest cache gap | **Fixed:** pin, obstruction, manifest and generation changes invalidate; relocation remains supported. |
| Case-distinct HDL/SPICE names | **Fixed:** independent a/A and y/Y waveforms/oracles survive simulation. |
| Flat opening MSB | **Fixed:** new sequence exercises all three levels on every output and positive/negative carry assert/release. |
| Expanded historical drawings / unlabeled cell raster | **Improved:** selected primitive, interactive cell/device mapping and real abutment are integrated. Remaining presentation work is findings 1–6 above. |

**22 targeted tests passed, zero failures/skips, in 13.15 s** on the frozen current-head
clone: `tests/extract/test_compact.py`, `tests/synth/test_flow_api.py`,
`notebook/tests/test_cache.py`, `notebook/tests/test_experiments.py`, and
`tests/sim/test_cells.py::test_case_sensitive_hdl_names_round_trip_through_ngspice`.
[Exact command/result](../../logs/review/round2/round1_fixes_result.json),
[test log](../../logs/review/round2/round1_fixes.log),
[publication/grid checks](../../logs/review/round2/data_checks.json).

No new full-suite or fresh-Colab execution was needed for this editorial round. No code,
notebook, figure, PDK or reference was edited by REVIEW; no packages installed or git state
changed by REVIEW beyond the explicitly requested scratch clone. Writes are confined to
this status and `logs/review/`. Review is complete; interface requests are the concrete
owner actions in findings 1–6, not additional scope/qualification prose.
