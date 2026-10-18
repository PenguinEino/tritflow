# Placeholder registry and integration contract

All reader-visible substitutions in the chapter files, teaser, pitch, captions,
repository README drafts, reuse appendix and official-repository PR draft are
listed below. They are specifications for FRONTEND's renderer, not attributes
already added to the Python API. Do not use Python `str.format` over whole
Markdown files: LaTeX has its own braces. Replace only the exact registered
tokens `{namespace.field}` and reject unresolved registered tokens.

Numbers in results, captions and badges come from these sources. Chapter
numbers, ternary definitions, equations, HDL syntax, unit conversions and
product names are structural constants, not experimental claims. The short
intro precedes chapter 0; teaser.md supplies its two-sentence figure caption.
Main text and figures go together; figures.md and predict_first.md are handoff
documents and are not inserted as notebook chapters.

Phase 2 makes the existing paper figures the primary heroes. Their fixed
four-trit example is the `paper_adder`/`paper_pnr` context below; the `adder`
context still means the separately executed default example. Retained original
tokens that are unused in the static chapters remain available to the optional
interactive specifications. They do not all have to appear in the main text.
Resolve captions and image inputs together; current numerical substitutions
cannot repair stale labels or curves already rendered into an image.

## Read and validation rules

1. Select one consistent context per figure/headline. For a fresh adder,
   `d = flow.load(ROOT/'examples/adder.tv', 'adder', {'N': N})`,
   `net = d.synthesize()`, `lay = net.place_and_route(...)`,
   `drc = lay.drc()`, `lvs = lay.lvs()`, and `post` is the actual
   `lay.extract().simulate(...)` result. Use `expected=` with the independent
   arithmetic oracle. These calls already exist; no code changes are requested
   outside FRONTEND ownership.
2. For width selections, use `scale = load_scaling(ROOT/'results/adder_scaling.json')`
   and `row = next(r for r in scale['rows'] if r['n'] == N)`. Validate the
   selected record and its consumed sources using the existing notebook
   `experiments.verify_publication_sources(row, ROOT, PDK_ROOT)` and the native
   artifact hashes. A loader alone is not source validation. Inspect
   `comparison_scope` and verify the identical-device/+wire-C experiment.
3. Load `grid = tritflow.sim.sizing.load_grid('INV')` for the INV estimate;
   `j` is a selected complete grid row and `a = grid['adopted_index']`.
   In the static chapter choose the longest common RP/RN length at adopted
   MP/MN dimensions among the finite plotted transfer curves, as specified
   in predict_first.md; no live selector is required.
   `z(j)` below means the unique `grid['rows'][j]['dc']` row with
   `input_trits == [0]`. `load_grid` validates sources/models/analysis.
4. Read the library generation before/after multi-file cell views; retry if
   it changes. Check current qualified PDK against
   `notebook/setup_pins.json: $.pdk_commit`. For `.char.json`, compare
   `source_sha256` to the actual extracted source and verify model hashes.
   Cell qualification uses recorded deck hashes, not the prose status file.
5. Success boxes in the chapters are success templates. Render them only after
   their referenced assertions pass. If unavailable, stale, failed or running,
   replace the whole success box with a concise status and reason, retaining
   that point in the figure/evidence table. Never substitute zero, a historical
   status-table number or a passing point from a different width. Null delay
   remains null. Unknown scope is not PASS.
6. Signed error and voltage use four significant digits; integer counts remain
   integers. Use µm and `width × height` for dimensions, fF/pF/ns/mV/µA/mW
   as stated. Do not include units twice. Percentages are 100 times the ratio.
   Keep native precision in every check. Meaningful failure states take
   precedence over display formatting.

JSON paths use `$` for the root; array selections are described explicitly.
Every derived field below states its formula. Names like `post`/`net` refer
to the real API results above and not invented JSON schemas.

## Context and trit levels

| Token | Exact source or calculation |
|---|---|
| `{history.tapeout_year}` | `docs/editorial.md`, “Context that belongs in the intro”, author-cell tapeout bullet; extract the year following “in” in that bullet (2026). Context fact, not a measured result. |
| `{history.delivery_month}` | Same section, “chip is expected in January 2027”; extract the month/year. The schedule is an expectation, never a silicon result. Reconcile with `docs/concept.md` chapter 9 if changed. |
| `{history.node_um}` | `docs/editorial.md`, same section, “NDA-free 1 µm CMOS PDK”; extract its stated process scale. This is PDK context, not a layout dimension measured in this notebook. |
| `{history.pdk_opened_year}` | Same bullet, “opened 2025”; extract the stated year. |
| `{levels.negative_v}` | `tritflow.TRIT_VOLTS[-1]`. |
| `{levels.zero_v}` | `tritflow.TRIT_VOLTS[0]`. |
| `{levels.positive_v}` | `tritflow.TRIT_VOLTS[1]`; display with a positive sign. |
| `{levels.band_v}` | `tritflow.PASS_BAND`; cross-check selected simulation conditions. |

## Opening adder and teaser

The live default uses N=2. A precomputed width uses the matching native
`row['artifacts_sha256']` entries, normally under
`build/adder_scaling/adder<N>/`. Read its gate JSON, PNR JSON and
`postlayout/post/measurements.json`/`simulation.json` after verifying hashes.
Do not imply `build/` ships with Colab; these native views must travel in a
verified record if width selection offers them.

| Token | Exact source or calculation |
|---|---|
| `{adder.width}` | Selected `N` passed to `flow.load`; recorded equivalent `row['n']`. |
| `{adder.hdl_lines}` | `len((ROOT/'examples/adder.tv').read_text().splitlines())`; includes blank/comment lines, counts only the displayed top-level file. Its included shared modules are named in the caption. |
| `{adder.cells}` | `net.report()['total_cells']`; recorded `row['cell_count']` or `len(GateNetlist.load(gate_json).instances)`. |
| `{adder.die_um}` | `lay.stats['die_size_um']`; recorded `row['die_size_um']`. Format each component with no unit, joined by ×. |
| `{adder.drc_items}` | `drc['violations']` from `Layout.drc()`; recorded PNR JSON `$.checks.pdk_drc.violations`. Verify `clean` and native report. Cell DRC's different `items` key does not apply here. |
| `{adder.lvs_status}` | “Match” only when `lvs['matched'] is True`; otherwise show its failure/unavailable status. Recorded native `postlayout/lvs.json: $.matched` and its strict report must agree with `row['lvs_matched']`. |
| `{adder.logic_vectors}` | `net.report()['equivalence']['vectors']`; recorded `row['synthesis_equivalence']['vectors']`. This counts checked source-to-cell vectors. The default's separate integer oracle exhausts `d.truth_table()`. Label sampled equivalence explicitly when a width exceeds exhaustive coverage. |
| `{adder.logic_mode}` | `net.report()['equivalence']['mode']`; recorded `row['synthesis_equivalence']['mode']`. Preserve exhaustive versus sampled wording. |
| `{adder.analog_states}` | `len(set(map(tuple, post['stimulus']['vectors'])))`; recorded `len(set(map(tuple, row['vector_plan']['vectors'])))`. Count unique input states including initialization, not total segments. |
| `{adder.analog_status}` | “PASS” only if `post['measurements']['passed']` and finite settling for every required transition/output; see `measurements.rows[*].outputs[*].settling_s`. Recorded `row['post_passed']` must agree with native measurements. |
| `{adder.load_ff}` | Exact scalar `load=` argument passed to `.simulate`, `LOAD_F` in the default notebook, multiplied by 1e15. Cross-check actual Cload values in `post['stimulus']['netlist']`; the stimulus has no `loads_f` field. Require equal output loads before using scalar wording. Recorded `row['conditions']['load_f']*1e15`. |

## Divider and sizing

`Vh`, `Ph` and their primed values are the explicit calculations in
predict_first.md. They are not new SIM entrypoints. Use INV selected at zero
for these numbers; switch to a gate-appropriate measured-only caption for
NANY. The new prediction implementation belongs to FRONTEND.

| Token | Exact source or calculation |
|---|---|
| `{divider.output_v}` | `Vh` from the MP/MN/RP/RN divider in predict_first.md, using baseline dimensions. |
| `{divider.power_mw}` | `Ph*1e3` from that calculation. |
| `{divider.spice_output_v}` | `z(a)['output_v']['Y']` from `cells/out/sizing/INV.grid.json: $.rows[$.adopted_index].dc`, selected by `[0]` input vector. |
| `{divider.spice_power_mw}` | `-1e3*sum(grid['conditions']['supplies_v'][r]*z(a)['rail_current_a'][r] for r in ('VDD','VMID','VSS'))`. |
| `{sizing.predicted_shift_mv}` | `(Vh_prime(j)-Vh)*1e3`, full primed divider, not the derivative approximation at large steps. |
| `{sizing.spice_shift_mv}` | `(z(j)['output_v']['Y']-z(a)['output_v']['Y'])*1e3`. |
| `{sizing.max_error_mv}` | `grid['rows'][j]['max_error_v']*1e3`. |
| `{sizing.current_ua}` | `grid['rows'][j]['max_static_current_a']*1e6`; maximum absolute rail current over DC states, not power. |
| `{sizing.adopted_error_mv}` | `grid['rows'][a]['max_error_v']*1e3`. |
| `{sizing.adopted_current_ua}` | `grid['rows'][a]['max_static_current_a']*1e6`. |
| `{sizing.adopted_rr_um}` | `grid['rows'][a]['dimensions']['RP']['l_um']`, asserted equal to RN's length. This is the adopted INV row in `cells/out/sizing/INV.grid.json`. |
| `{sizing.selected_rr_um}` | `grid['rows'][j]['dimensions']['RP']['l_um']`, asserted equal to RN's length, for the longest finite transfer variant at the same MP/MN dimensions. |
| `{sizing.selected_current_ua}` | `grid['rows'][j]['max_static_current_a']*1e6`; assert that this value agrees with the zero-input absolute rail-current maximum for this fixed-MOS INV comparison before calling it the measured middle-level current. |
| `{sizing.selected_error_mv}` | `grid['rows'][j]['max_error_v']*1e3`, the worst logical-level error over all discrete inputs of the same longer-RR INV variant. |

## Standard-cell comparison

For the static `fig_cell` hero set `C = 'NANY'`; optional interactive views may
select a different cell with their own caption. Let `abstract` be
`cells/out/<C>/<C>.abstract.json`, and `eq` be
`cells/out/equivalence_report.json`. `pc = eq['parasitic_aware']['cells'][C]`.
Use only reference logic cells INV/NAND/NOR/NANY for this success box.
BUF is a two-INV reference construction; ties/FILL have no taped-out counterpart
and instead show their dimensions and own qualification, with no area ratio.

| Token | Exact source or calculation |
|---|---|
| `{cell.name}` | `abstract['name']`. |
| `{cell.width_um}` | `abstract['width']`. |
| `{cell.height_um}` | `abstract['height']`. |
| `{cell.area_ratio}` | `abstract['width']*abstract['height']/reference['cells'][C]['area_um2']`, where reference is `notebook/narrative/reference_geometry.json`. Its source GDS SHA must equal `eq['schematic_equivalence'][C]['original_gds_sha256']`. The file was generated from actual reference `Layout.cell(top).dbbox()`; it is not a hand-entered area table. |
| `{cell.compare_load_ff}` | `pc['transient']['original'][K]['load_f']*1e15`, `K='10f'` initially; require the compact record to have the same load, ramps, windows, directed cases and model coefficients. |
| `{cell.original_settling_ns}` | `pc['transient']['original'][K]['max_settling_s']['Y']*1e9`. |
| `{cell.compact_settling_ns}` | `pc['transient']['compact'][K]['max_settling_s']['Y']*1e9`. |
| `{cell.settling_change_pct}` | `100*(compact/original-1)` using those unrounded delays; keep sign. This compares maxima, not a same-transition penalty. |

Validate both schematic-equivalence proofs, all compared source/model/GDS
hashes and `parasitic_aware.passed`. The historical report is not current
pinned qualification until its inputs/decks have been checked. Copying only
these narrative files into a submission requires also bundling the small
reference_geometry.json if the area comparison is retained.

## Arithmetic and synthesis

`ha = flow.load(ROOT/'examples/half_add.tv', 'half_add').synthesize()`;
`fa = flow.load(ROOT/'examples/full_add.tv', 'full_add').synthesize()`.
Use FA's independent identity oracle before its success caption. For chapter
5 let `graph_net` be the exact netlist shown, not the opening adder by assumption.

| Token | Exact source or calculation |
|---|---|
| `{arithmetic.ha_nany}` | `ha.report()['cells'].get('NANY', 0)`. |
| `{arithmetic.ha_inv}` | `ha.report()['cells'].get('INV', 0)`. |
| `{arithmetic.fa_nany}` | `fa.report()['cells'].get('NANY', 0)`. |
| `{arithmetic.fa_inv}` | `fa.report()['cells'].get('INV', 0)`. |
| `{arithmetic.fa_vectors}` | `3**len([p for p in fa.ports if p.dir == 'input'])`; assert all vectors satisfy `a+b+cin == sum+3*cout` in source and mapped evaluation before display. |
| `{synth.top}` | `graph_net.top`. |
| `{synth.cells}` | `graph_net.report()['total_cells']`. |
| `{synth.depth}` | `graph_net.report()['logic_depth']`. |
| `{synth.equivalence_mode}` | `graph_net.report()['equivalence']['mode']` (exhaustive or the actual sampled mode). |
| `{synth.equivalence_vectors}` | `graph_net.report()['equivalence']['vectors']`. |
| `{synth.equivalence_status}` | “passes” only if `graph_net.report()['equivalence']['passed']`; otherwise failure text instead of the success box. |

## Placement and routing

These fields all use the same selected `lay` as its hero geometry.
If reopening native data, use `flow.load_layout(net, directory)` and validate
the native reports; loading a layout alone is not a new check.

| Token | Exact source or calculation |
|---|---|
| `{pnr.die_um}` | `lay.stats['die_size_um']`, components joined by ×. |
| `{pnr.utilization_pct}` | `100*lay.stats['utilization']`. |
| `{pnr.wirelength_um}` | `sum(lay.stats['wirelength_um'].values())`; this is the recorded signal-wire metric by metal. |
| `{pnr.initial_hpwl_um}` | `lay.data['history'][0]['hpwl']`, cell-terminal HPWL. |
| `{pnr.final_hpwl_um}` | `lay.data['history'][-1]['hpwl']`, same metric. |
| `{pnr.drc_items}` | `lay.data['checks']['pdk_drc']['violations']` after checking `clean` and native DRC hashes. |
| `{pnr.lvs_status}` | Strict `lay.lvs()['matched']` mapped to “Match”; use retained verified LVS evidence for recorded views. |

## Width and load results

`fits = tritflow.sim.scaling.fit_scaling(scale)`; recompute after validation
instead of trusting a potentially stale saved fit. `row` is the selected
complete passing width, initially the largest displayed N for the static
chapter. Show actual widths used in every fit; retain failed
or running rows in the overview. `sweep = load_sweep_results(ROOT/'results/full_add_load_sweep.json')`
also needs `verify_publication_sources` and native artifact checks.

| Token | Exact source or calculation |
|---|---|
| `{scaling.selected_n}` | `row['n']`. |
| `{scaling.predicted_ns}` | `th(row['n'])*1e9` from the single-slice estimate in predict_first.md. |
| `{scaling.device_ns}` | `row['carry']['pre']['max_settling_s']*1e9`. |
| `{scaling.wired_ns}` | `row['carry']['post']['max_settling_s']*1e9`. |
| `{scaling.device_slope_ns}` | `fits['carry']['pre']['slope']*1e9`; require a finite fit and show its actual width set. |
| `{scaling.wired_slope_ns}` | `fits['carry']['post']['slope']*1e9`; same width/mode checks. |
| `{scaling.predicted_power_mw}` | `Ph_zero(row['n'])*1e3` from per-cell zero-bias signed DC powers and actual mapped counts, predict_first.md. |
| `{scaling.zero_power_mw}` | Native artifact `postlayout/static.json`, unique all-zero `input_trits` row, `static_power_w*1e3`, resolved via selected row's `artifacts_sha256`. If that artifact is not distributed, omit the zero-state measured comparison sentence; never use the maximum as a substitute. |
| `{scaling.power_per_cell_mw}` | `fits['static_power']['slope']*1e3`; an adder-mix effective slope for tested-state maxima. |
| `{scaling.static_states}` | `row['static_vector_count']`. |
| `{scaling.max_power_mw}` | `row['static_power_worst_w']*1e3`. |
| `{scaling.rail_deviation_mv}` | `row['max_rail_deviation_v']*1e3`; separate rail-network calculation. |
| `{scaling.zero_shift_mv}` | `row['max_zero_shift_v']*1e3` from that network, not waveform measurements. |
| `{scaling.current_utilization_pct}` | `row['em_check']['max_utilization']*100`; scope is width-scaled DC limits, not manufacturing signoff. Obtain reserved-margin threshold separately from the matching PNR `$.power.assumptions.reserved_current_margin`. |
| `{load.hold_ns}` | `sweep['conditions']['hold_s']*1e9`. |
| `{load.last_pass_pf}` | `sweep['boundary']['last_pass_f']*1e12`, only if `boundary_found` and both endpoints are finite and their measured rows agree. |
| `{load.first_fail_pf}` | `sweep['boundary']['first_fail_f']*1e12` under the same checks; this is a measured bracket, not a universal load limit. |

No-boundary wording replaces the entire bracket sentence: “The measured
loads and their pass/fail states are shown for the stated input interval.”
Never format null into a numerical endpoint.

## Edited circuit

Use the current `custom`, `planned`, `custom_out` and `custom_result` in the
existing notebook's `load_edited`/`complete_design` path. Regenerate the figure
from the edited source, never a catalog illustration left over from before
the edit. Require both source and cell logic to match the integer oracle.

| Token | Exact source or calculation |
|---|---|
| `{custom.name}` | `custom.top`; include the selected `DESIGNS[CHOICE].description` beside it. |
| `{custom.logic_states}` | `len(planned)`, after asserting unique/exhaustive vectors for the selected input ports and successful oracle checks. |
| `{custom.cells}` | `custom.report()['total_cells']`. |
| `{custom.die_um}` | `custom_result['stats']['die_size_um']`, components joined by ×. |
| `{custom.drc_items}` | `custom_result['drc']['violations']`, with `clean` verified. |
| `{custom.lvs_status}` | `custom_result['lvs']['matched']` mapped to “Match”. |
| `{custom.analog_states}` | `len(set(map(tuple, custom_result['post']['stimulus']['vectors'])))`; assert against planned state coverage. |
| `{custom.analog_status}` | “PASS” after `experiments.assert_experiment(custom_result)` and its output/state checks; otherwise show failure context instead of this success box. |

## Evidence appendix

These are formatted summaries, often strings. Each includes scope, revision
and fresh/recorded status where relevant. It is acceptable and required to say
“unavailable for this revision” when no matching source exists.

| Token | Exact source or calculation |
|---|---|
| `{evidence.source_commit}` | Current notebook `SOURCE_COMMIT`, resolved by `git -C ROOT rev-parse --verify HEAD^{commit}`; label an exported tree without git explicitly. A badge tag is not the resolved revision. |
| `{evidence.pdk_commit}` | `tritflow.sim.provenance.pdk_provenance(PDK_ROOT)['qualified_commit']`, asserted equal to setup pin and actual consumed deck/model hashes. |
| `{evidence.tools}` | Live `runtime_fingerprint(ROOT, PDK_ROOT)` tool-version entries, or `sys.version`, `importlib.metadata.version('klayout')`, and actual `klayout -v`/`ngspice --version` stdout using configured executable paths. Keep recorded-experiment tool versions separate; pins alone are not installed versions. |
| `{evidence.cell_checks}` | `cells/out/verify_report.json: $.cells` and `$.passed`, per-cell `drc.items`, `lvs.passed`, `dc.passed`. Validate `$.artifact_sha256` and `$.deck_sha256`; retain FILL's documented probe-fixture/empty-extraction qualification instead of inventing ordinary LVS. |
| `{evidence.sizing_checks}` | `cells/out/sizing/{INV,NANY}.grid.json: $.rows`, counts of total candidates, finite error/current pairs, `passed`, errors outside the band and unavailable rows with `$.rows[*].error`. List unavailable rows and their dimensions/reasons explicitly; finite points alone cannot prove every candidate passed. |
| `{evidence.abutment_checks}` | Same report `$.abutment.ordered_pair_orientation_cases`, `.items`, `.passed`; these count ordered pair/orientation cases, not unique pairs only. |
| `{evidence.adder_checks}` | Selected adder native `drc`, `lvs`, `post['measurements']` plus the synthesis equivalence report, with the separate logic/state/transition counts. |
| `{evidence.width_checks}` | `results/adder_scaling.json: $.rows[*]`, fields n/state/passed/drc_clean/lvs_matched/pre_passed/post_passed/error, with `vector_plan`/`synthesis_equivalence` scope. Include incomplete rows. |
| `{evidence.load_checks}` | `results/full_add_load_sweep.json: $.rows[*]`, load_f/passed/unsettled/failures and `$.boundary`, `$.conditions`; include failing rows. |
| `{evidence.routing_checks}` | `build/pnr_fuzz/summary.json: $.completed`, `.passed`, `.failed`, `.inputs_stable`, `.cases[*]`; verify its fingerprint and each `fuzz.result.json` native evidence using `examples/fuzz_pnr.py`'s recorded method. No matching distributed summary means “unavailable”, not the historical count. |
| `{evidence.tests}` | A selected matching-revision JUnit XML, e.g. `build/sim_verification/pytest.xml`, via `xml.etree.ElementTree.parse(path)` and `testsuite` tests/failures/errors/skipped attributes, plus command, source revision and timestamp. Do not combine older stream totals into a supposed current full-suite count. `logs/review/pytest.xml` concerns the frozen review revision only. |
| `{evidence.colab_status}` | Read `notebook/colab_verified.json` and its linked `docs/status/COLAB.md` report; verify `publish`, `passed`, notebook/evidence hashes and the named tested source. State that revision, completed cells, attempt count and `timing_scope` together. The current successful retry excludes the initial setup attempt and retry gap; it is not an uninterrupted cold-install time. Label a historical success as historical and state that it does not verify the current revision. Without a matching successful observation, do not claim current-revision Colab verification. The legacy `logs/colab/run-timing.json` failure/manual-follow-up value remains unsuitable as a success benchmark. |
| `{evidence.session_seconds}` | `time.monotonic()-started` in the closing notebook cell, where `started` is set before setup. Label actual environment and completion; local or failed/manual elapsed time is not a successful clean-Colab benchmark. |

## Integration requests and optional material

- FRONTEND should package/reopen native width GDS, PNR and waveform views for
  every offered width. The current summary JSON is enough for scaling points,
  not for substituting another width's GDS/waveform or zero-state DC result.
- The generated `reference_geometry.json` is a small portable replacement for
  requiring the author's full reference checkout just to show footprint ratios.
  Its source hashes already match the independent equivalence report at authoring.
- Successful release and real-Colab evidence replace the appendix's truthful
  unavailable state only when those actual checks have been completed.
- Phase 4 includes the validated STA and framed-top results as labelled
  recorded evidence. Resolve their new contexts below, or replace their whole
  result blocks with unavailable status. Corner sweeps remain optional. Give
  every included study its actual conditions, coverage and approval scope.

## Paper-figure source contexts

The following additional tokens are for fixed static figures and their
captions. They are kept separate from notebook variables that may refer to a
different design. Every numeric token must come from the exact input used in
the regenerated image, not from `figures/README.md`'s draft caption.

### Fixed opening adder and placement

Read `report = JSON('build/adder4/adder4.report.json')`,
`physical = JSON('build/adder4/adder4.pnr.json')`,
`proof = JSON('build/adder4/adder4.lvs.summary.json')` and the matching
`build/adder4/adder4.json` gate netlist. Confirm real drawing DRC and strict
LVS reports, GDS/library hashes and the associated extracted simulation.
`fig_flow.py` and `fig_pnr.py` read these exact files.

| Token | Exact source or calculation |
|---|---|
| `{paper_adder.width}` | Number of scalar input ports named `a[...]` in `build/adder4/adder4.json: $.ports`, asserted consistent with the `N` used for this build and the illustrated sum MSB. |
| `{paper_adder.hdl_lines}` | `len(Path('examples/adder.tv').read_text().splitlines())`, the same operation used in `figures/fig_flow.py`; shared module files are additional inputs. |
| `{paper_adder.nany}` | `report['cells']['NANY']`. |
| `{paper_adder.inv}` | `report['cells']['INV']`. |
| `{paper_adder.cells}` | `report['total_cells']`, cross-check actual gate instances. |
| `{paper_adder.equivalence_mode}` | `report['equivalence']['mode']`, with `passed` asserted. |
| `{paper_adder.die_um}` | `physical['die']`, components joined with × and checked against its GDS boundary. |
| `{paper_adder.drc_items}` | `physical['checks']['pdk_drc']['violations']`, require present numeric count, `clean` and matching report. Missing is not zero, regardless of the script's older fallback. |
| `{paper_adder.lvs_status}` | “Match” only when `proof['matched']` and actual strict-port/native report evidence agrees. |
| `{paper_pnr.initial_hpwl_mm}` | `physical['history'][0]['hpwl']/1e3`. |
| `{paper_pnr.final_hpwl_mm}` | `physical['history'][-1]['hpwl']/1e3`. |
| `{paper_pnr.hpwl_reduction_pct}` | `100*(1-physical['history'][-1]['hpwl']/physical['history'][0]['hpwl'])`; require positive initial HPWL. |

### DC and sizing panels

For the precise INV point in `fig_gates`, run the same public call as its
script: `dc_transfer(Path('cells/out/INV/INV.ext.spice').read_text(), 'INV',
['A'], ['Y'], 'A', fixed_trits={}, step_v=0.02)`.
Let `q = result['data']` and choose `i = argmin(abs(q['v-sweep']))`, asserting
the sample is at VMID to numerical tolerance. Both the figure and the source
use the nominal bench temperature; verify it against the characterized source.
The call does not retain the full figure curves in a portable JSON; save its
conditions/results with the final figure render if the exact point is needed
without rerunning SPICE. Existing char zero-input DC rows can cross-check it.

Let `gi`/`gn` be validated INV/NANY sizing grids. A finite plotted row has both
`max_error_v` and `max_static_current_a` present and finite. Count unavailable
candidates separately in Appendix B. Do not infer all-pass from the plot title.

| Token | Exact source or calculation |
|---|---|
| `{paper_gates.temperature_c}` | Nominal `build_testbench`/`dc_transfer` temperature, cross-checked with `cells/out/INV/INV.char.json: $.conditions.temperature_c`; require equal conditions for all four displayed cells. |
| `{paper_gates.inv_zero_v}` | `q['v(y)'][i]` at that zero-input sample. |
| `{paper_gates.inv_current_ma}` | `abs(q['i(vdd)'][i])*1e3`; this is the lower-panel metric, not a sum of rail currents. |
| `{paper_gates.inv_power_mw}` | `-1e3*sum(V[r]*q['i('+r.lower()+')'][i] for r in ('VDD','VMID','VSS'))`, using the actual nominal `tritflow` rail values. |
| `{paper_sizing.resistor_lengths_um}` | Sorted unique `rows[*].dimensions.RP.l_um` for the INV transfer subset with MP and MN dimension maps equal to the adopted maps and nonempty `transfer`; join as a list. Cross-check RN's matching length and the displayed curves. |
| `{paper_sizing.inv_count}` | Count finite plotted rows in `cells/out/sizing/INV.grid.json: $.rows`. |
| `{paper_sizing.nany_count}` | Count finite plotted rows in `cells/out/sizing/NANY.grid.json: $.rows`; one unavailable candidate at inspection must not count as a finite point or a pass. |
| `{paper_sizing.nany_error_mv}` | `gn['rows'][gn['adopted_index']]['max_error_v']*1e3`. |
| `{paper_sizing.nany_current_ua}` | `gn['rows'][gn['adopted_index']]['max_static_current_a']*1e6`. |
| `{paper_sizing.error_floor_mv}` | The explicit plotting floor passed as `floor_mv` to INV `scatter` in `figures/fig_sizing.py: make`; a display setting, not a measurement. Below-floor triangle points retain their unmodified measured values in data. |

### Cell and arithmetic panels

| Token | Exact source or calculation |
|---|---|
| `{paper_cell.original_die_um}` | `notebook/narrative/reference_geometry.json: $.cells.NANY.bbox_um`; width = x1-x0, height = y1-y0, joined by ×. Its GDS SHA must match the independent reference proof as above. |
| `{paper_cell.row_count}` | `len(ROW)` in `figures/fig_cell.py`, currently the INV/NAND/NOR/NANY sequence; validate those actual GDS references and aligned rails. |
| `{paper_synth.ha_cells}` | `flow.load('examples/half_add.tv','half_add').synthesize().report()['total_cells']`; this is the graph used in `fig_synth`, not the full-adder hierarchy's count. |

The existing `cell.*` tokens use fixed NANY for this figure, while
`arithmetic.*` comes from current synthesis of the actual two module sources.
The shown arithmetic vector is an illustration of the radix identity;
full coverage still requires the independent truth-table checks.

### Post-layout and width panels

For `fig_postlayout`, load `ps = JSON('build/full_add/postlayout/summary.json')`,
`mp = JSON('build/full_add/postlayout/pre/measurements.json')` and
`mw = JSON('build/full_add/postlayout/post/measurements.json')`.
Choose `k` exactly as the script does: the index after initialization with
largest finite `mw['rows'][k]['outputs']['sum']['settling_s']`.
Failing or unsettled measurements must not be coerced to zero to select a
passing-looking zoom. Compare the same row k in both runs, with matching
input history, ramp, load and device fingerprint. The current comparison is
device-only versus devices+wire-C; “schematic” is the wrong baseline name.

| Token | Exact source or calculation |
|---|---|
| `{paper_post.states}` | `len({tuple(r['input_trits']) for r in mw['rows']})`; cross-check all expected full-adder states and the load-sweep input set. |
| `{paper_post.hold_ns}` | `ps['hold_s']*1e9`. |
| `{paper_post.load_ff}` | `ps['output_load_f']*1e15`, cross-checked against actual Cload devices in each retained bench. |
| `{paper_post.pre_sum_ns}` | `mp['rows'][k]['outputs']['sum']['settling_s']*1e9`. |
| `{paper_post.post_sum_ns}` | `mw['rows'][k]['outputs']['sum']['settling_s']*1e9`. |
| `{paper_scaling.width_min}` | Minimum `n` of the complete, passing, validated rows displayed from `results/adder_scaling.json: $.rows`. |
| `{paper_scaling.width_max}` | Maximum `n` of those same displayed rows; show the full actual width set in Appendix B, since a range alone could hide a gap. |
| `{paper_scaling.load_ff}` | `rows[*].conditions.load_f*1e15`, asserted equal across the displayed width series. |

The existing `scaling.*`/`load.*` tokens retain their exact current source
definitions. All displayed rows must be complete and passing before calling
the series DRC/LVS checked and simulated. Use free-intercept fits to the same
rows as the plotted points. Do not reuse old printed slopes; do not silently
drop failed widths. The maximum static-power caption refers only to the
documented sampled DC states, not all possible inputs of a wide adder.

## Public README and official-repository PR substitutions

`readme_final.md` supersedes `readme_draft.md` for the public source repository's
root README; both files' links resolve from that destination. `pr_description.md` has
the proposed PR title as its first heading and the reviewable body below.
The exact author block is copied from docs/author.md in both drafts. No phone
number, membership, attendance or approval status is inferred.

| Token | Exact source or calculation |
|---|---|
| `{release.colab_url}` | Construct the Colab URL from the public repository and selected immutable ref, using `submission/ISSCC27/submitted_notebooks/TritFlow/build-info.json: $.release.default_ref` only after `$.release.compatible` and `$.release.matches_source_notebook` are true for this submitted source. Otherwise omit the badge/link and show the explicit unavailable release state; do not emit the known-incompatible old tag as a ready launch. |
| `{release.source_commit}` | Same build-info `$.source_commit_at_bootstrap`, after checking `$.source_notebook_sha256` against the submitted notebook's source and `$.capture.source_sha256`. Do not substitute a newer packaging or working-tree commit for the executed source identity. |
| `{release.capture_status}` | Same build-info `$.capture.completed`, `$.capture.elapsed_s`, `$.source_notebook_sha256` and `$.capture.source_sha256`; format completion/environment/scope only after matching the actual submitted notebook source. If stale, say “No matching execution recorded for this submitted source.” Tools recorded only at packaging must retain `$.tools_observation` scope. |

`evidence.colab_status` must match the selected submitted-source revision in
these public drafts, and `evidence.tests` must state its own scope/revision.
The legacy payload must not be promoted through a later historical Colab
success; the selected submitted source still needs its own matching evidence.
Keep the appropriate unavailable text when that record is absent. Proposed
filing scope is only the TritFlow project folder; no actual
official-repository diff or PR is asserted or created by this text draft.

## Phase 3 — identify routing realizations and explain the sizing comparison

The signs in `sizing.predicted_shift_mv` and `sizing.spice_shift_mv` must be
preserved. Chapter 2 now says explicitly that the simplified divider gets the
current-reduction trend right but misses the direction of the small zero-level
shift. Its measured current/error endpoints come from the adopted and selected
INV grid rows above, not from the hand model's currents. The actual substrate
connections are `tritflow.cells.circuits.circuits()['INV'].resistors` (RP and
RN both have well/substrate VDD), cross-checked with
`cells/out/INV/INV.spice` XRP/XRN terminal order. Bias terms are in
`$TR1UM_PDK/libs.tech/spice/models/models_IP62_res_v5.lib`, `F_RR`'s dedicated
width branch; `notebook/predictions.py:divider` retains only its geometry
polynomial and constant MOS on-resistance. Do not imply a quantitative split
of the mismatch among nonlinear terms without a separate controlled experiment.

Use a compact visible identifier of the form `data-set/circuit · seed <value>`.
Seed alone is not an artifact identity: retain the matching GDS/PNR digest with
the evidence, and do not copy a seed from another build with the same top name.

| Token | Exact source or calculation |
|---|---|
| `{paper_adder.run_id}` | `paper/` + `build/adder4/adder4.json: $.top` + ` · seed ` + `build/adder4/adder4.pnr.json: $.seed`. Verify the PNR and GDS hashes against the paper figure's native evidence. The inspected value is `paper/adder4 · seed 7`. |
| `{paper_post.run_id}` | `paper/full_add · seed ` + `build/full_add/full_add.pnr.json: $.seed`. Its digest must match `build/full_add/postlayout/summary.json: $.input_sha256[absolute PNR path]`; that summary must match the paper's saved native summary hash. Retain the GDS digest too. The inspected value is `paper/full_add · seed 19`, distinct from the archive despite equal die dimensions. |
| `{paper_scaling.run_id}` | `width-sweep · seed ` + the common seed from `results/adder_scaling.json: $.rows[*].seed`, only if all displayed widths share it. Otherwise list each `(n,seed)` pair. Verify the N=4 GDS identity against the paper-adder view before treating it as the same realization. The inspected widths all use seed 7. |
| `{archive.adder_run_id}` | Read `adder4/adder4.pnr.json: $.seed` inside `notebook/assets/four_designs.zip`, validate the member against `manifest.json: $.files['adder4/adder4.pnr.json']`, and format `four-design/adder4 · seed <value>`. |
| `{archive.full_add_run_id}` | Same archive, `full_add/full_add.pnr.json: $.seed`, with its matching manifest member hash; format `four-design/full_add · seed <value>`. |
| `{archive.mac1_run_id}` | Same archive, `mac1/mac1.pnr.json: $.seed`, with its matching manifest member hash; format `four-design/mac1 · seed <value>`. |
| `{archive.mul1_run_id}` | Same archive, `mul1/mul1.pnr.json: $.seed`, with its matching manifest member hash; format `four-design/mul1 · seed <value>`. |

For portable notebook rendering, FRONTEND must preserve the verified native
paper seeds/GDS identities in `notebook/assets/paper_evidence.json` alongside
their existing measurement records; the runtime must not require `build/`.
The current saved `paper_pnr`/`paper_post` subsets do not carry those seed
fields. This is a requested addition by their owner, not an EDITOR write to
that snapshot. The archive already carries each full native PNR record.

Populate these tokens in `notebook/editorial.py:context`, together with the
four new sizing endpoint fields. Render the new Appendix B routing table
before insertion: the current generator renders captions/chapters but inserts
Appendix B prose without general token substitution after removing its old
summary table. Also add **Routing realization** to every generated physical
and per-output timing row, rather than relying only on a nearby prose note.
For a fresh replacement of an archived experiment, derive its actual seed
from that run's PNR/options and label it fresh; do not claim the archive's
identity when its geometry or options differ.

## Phase 4 — STA, framed top, reuse and final README

### STA comparison

Let `sta = JSON('results/sta/validation.json')`. Use schema 4 or a reviewed
compatible successor and require `complete`, `qualified_current` and
`stable_snapshot`. Verify its `source_sha256`, `sta_code_sha256`, cell generation
and timing-table inputs, plus each design's native SPICE/load/PNR evidence.
The inspected report is complete and current but `accuracy_passed` is false:
the outlier must remain visible. This is a successful validation with a stated
exception, not an all-output accuracy pass.

The scatter in `figures/fig_sta.py` uses each
`sta['designs'][*]['outputs'][*]['tested_predicted_s']` against `simulated_s`,
converted from seconds to ns. Each point is an output maximum over the same
tested transition set; the independently selected predicted and measured maxima
need not occur on one identical transition. Never describe it as one paired
worst transition. `predicted_s` is the separate conservative window estimate.
The API illustration uses the reader's actual `vectors`, scalar output
`load_f`, input-ramp `ramp_s` and logical-net `wire_caps` dictionary; it does
not execute the stored figure's whole
multi-design validation in one call. For unequal output loads use the API's
per-output load dictionary instead of scalar wording.

Populate `wire_caps` in the collapsed helper by taking
`reference_net_map(lvs['report'], net.top)` from `tritflow.extract` and looking
up each mapped net's `capacitance_f` in the actual GDS-derived capacitance
report, as `tritflow/sta/validate.py:_validate_design` does. Require all logical
nets to map. Passing `layout.data` alone instead invokes the separate
PNR-geometry wire estimator and would not reproduce the stated matched-load
validation. The short visible code receives this dictionary rather than
displaying that report-mapping plumbing.

| Token | Exact source or calculation |
|---|---|
| `{sta.within_target}` | `sta['outputs_within_target']`; cross-check the count of finite output rows with `abs(tested_error_percent) <= sta['accuracy_target_percent']`. |
| `{sta.output_count}` | `sta['statistics']['sim_endpoint_pairs']['count']`; require equality with the number of finite compared `tested_predicted_s`/`simulated_s` output pairs. |
| `{sta.target_pct}` | `sta['accuracy_target_percent']`. |
| `{sta.mape_pct}` | `sta['statistics']['sim_endpoint_pairs']['mean_absolute_percent_error']`; cross-check `mean(abs(100*(tested_predicted_s/simulated_s-1)))` over those output rows. This is a percentage, not the mean error in ns. |
| `{sta.outlier_endpoint}` | For the unique inspected `sta['outside_accuracy_target']` row, join `design` and `output` with `/`. If a later report has several exceptions, replace the singular sentence with the complete list; never select one silently. |
| `{sta.outlier_error_pct}` | The same row's signed `error_percent`; the current positive value supports “overpredicted.” If the sign changes, change that word. |
| `{sta.bound_mean_factor}` | `sta['worst_case_validation']['pessimism_vs_output_maxima']['mean_factor']`; cross-check the mean of `predicted_s/simulated_s` over compared outputs. Preserve the separate finite nominal-case coverage and `certified_analog_bound` scope. |
| `{sta.run_ids}` | For every `sta['designs']` row, select its native `<design>.pnr.json` path in `sta['source_sha256']`: `build/adder_scaling/<design>/...` for group `scaling`, `build/<design>/...` for group `example`. Verify its digest and corresponding GDS, then format `STA <group>/<design> · seed <pnr['seed']>`. The examples consume the paper routes, not the four-design ZIP. Common seeds may be grouped only with an explicit list/range of the included designs. Retain each individual identity on Appendix B output rows. |
| `{evidence.sta_checks}` | Format the validated report's matched count, target, MAPE, all `outside_accuracy_target` rows and `accuracy_passed`; separately give conservative mean factor, `worst_case_validation.case_count`, `.transition_case_count`, `.underprediction_count`, `.all_slew_domains_closed` and `.certified_analog_bound`. Link the exact validation and per-design tested/global reports with source identity, nominal conditions, loads, input plans and routing realizations. Do not substitute the conservative estimate into the scatter's accuracy summary. |

### Full-chip wrapper

The chapter-9 and README result is the canonical paper adder's separate wrapper,
not the taller seed-zero archived core. Read
`chip_data = JSON('build/adder4/chip/tr_1um_adder4.chip.json')` and
`signoff = JSON('build/adder4/chip/signoff/signoff.summary.json')`. Verify the
source core's GDS/PNR identity, frame source digest and pinned PDK, consumed
rules/binary/reference and produced reports/masks using PNR's recorded
input/output verification. `clean` and `physical_checks_passed` are true in
the inspected report; `submission_ready` is false. They are separate claims.

| Token | Exact source or calculation |
|---|---|
| `{chip.die_um}` | `chip_data['stats']['die_size_um']`, components joined by ×, cross-check the actual frame boundary and `chip_data['die']`. |
| `{chip.pad_count}` | `chip_data['stats']['pad_count']`, require agreement with `signoff['provenance']['frame']['pad_count']` and the actual pad map. |
| `{chip.drawing_drc_items}` | `signoff['drawing_drc']['violations']`, require `clean` and a verified native report. Counts include warnings/visited items under the report's stated policy. |
| `{chip.lvs_status}` | “Match” only when `signoff['drawing_lvs']['matched']` and `strict_ports` are true, with the actual native device/port report. This is drawing LVS before mask-data preparation. |
| `{chip.mask_drc_items}` | `signoff['mask_drc']['violations']`, require `clean` and the native post-MDP mask-DRC report; no waiver or missing-as-zero fallback. |
| `{chip.precheck_status}` | “Pass” only if `signoff['mpw_precheck']['clean']` is true and `exit_code == 0`, with the inspected template and retained log. |
| `{chip.submission_ready}` | Lowercase JSON boolean from `signoff['submission_ready']`; retain its reason and remaining external approvals. If absent, say unavailable; do not infer it from `clean`. |
| `{evidence.chip_checks}` | Format the above results plus source core run identifier, wrapper GDS identity, frame/pad map, MDP output, actual drawing/mask reports, MPW template/precheck, and `submission_ready`/reason. Preserve `mask_lvs.defined=false`, `matched=null` as “No post-mask LVS stage defined.” Do not convert null to Match. Include the full-adder wrapper only as a separately identified row with its own evidence. |

The visible code calls `layout.result.to_chip()` (the `PnrResult` API) and then
the returned `ChipResult.signoff()`. `flow.Layout` currently has no `to_chip`
convenience method. `Layout.signoff()`/`PnrResult.signoff()` concern the macro,
not a frame. Select the canonical compatible paper layout for the recorded
demo, not whichever live/archived result happens to have the same top name.
Use `library=`, `pdk_root=` and `klayout_binary=` explicitly with nondefault
settings: the low-level wrapper is not a `flow.Settings` delegate. Check and
display assertions/report identities in Appendix B or collapsed helper cells,
not in the chapter's short method example.

The native chip artifacts are currently under ignored `build/`. FRONTEND must
export/reopen a verified portable subset for the recorded chapter; reading a
status prose line is not a runtime replacement. The STA JSON is committed but
its native consumed sources also need portable identity/coverage information.
Do not start a new physical run or regenerate a figure merely to insert prose.
The release step alone redraws figures, before capturing their hashes.

### Installation and named Colab observation

| Token | Exact source or calculation |
|---|---|
| `{reuse.source_ref}` | The selected public immutable source commit containing this API and its repository assets. For a frozen clean checkout use its resolved `SOURCE_COMMIT` / `git rev-parse --verify HEAD^{commit}`, after the release owner checks that the commit is publicly fetchable and contains the rendered guide. Require a full hexadecimal commit before inserting into the pip VCS URL. This is the source to install, not automatically the older Colab-tested commit or the source stored in an unrelated submission payload. If unavailable, replace the install block with the release's explicit unavailable state. |
| `{colab.source_commit}` | `notebook/colab_verified.json: $.commit`, after checking `publish`, `passed`, referenced report and evidence/notebook hashes. It names a historical observation, not current-source verification. |
| `{colab.code_cells}` | Same named record, `$.passed_code_cells`, consistent with its per-cell log. |
| `{colab.seconds}` | Same record, `$.run_all_seconds_including_setup`, interpreted with `$.timing_scope`; in the inspected record it means the successful second Run all only, excluding the initial setup attempt and retry gap. The field name alone must not override this scope. |

`readme_final.md` supersedes the earlier public README draft and includes a
source-specific historical Colab paragraph. Its retry wording is valid for
the current record (`run_all_attempts=2`, `first_attempt_completed=false`);
if those change, replace the whole paragraph with wording for the actual run.
Do not promote it to a current-revision or uninterrupted-install claim. The
Colab badge still requires the independent compatible-release guard above.

Appendix C and the README share the same exactly seven-line API example.
Its `N=2`, zero vector, `100e-15` load and CLI seed are chosen example inputs,
not measured result claims. The steady-state smoke test is explicitly
distinguished from the notebook's independent arithmetic oracle and transition
coverage. Editable VCS installation is deliberate: `pyproject.toml` discovers
`tritflow*` packages, while cell/example/notebook data are repository assets.
The native tools and pinned PDK still need setup. README links are root-relative;
when Appendix C is inserted into the notebook, preserve code paths relative
to the source root and rebase any narrative-source links appropriately.
