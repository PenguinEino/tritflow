# Placeholder registry and integration contract

All reader-visible substitutions in the chapter files, teaser and pitch are
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

## Standard-cell comparison

Let `C` be the selected cell, `abstract` be
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
complete passing width. Show actual widths used in every fit; retain failed
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
| `{evidence.abutment_checks}` | Same report `$.abutment.ordered_pair_orientation_cases`, `.items`, `.passed`; these count ordered pair/orientation cases, not unique pairs only. |
| `{evidence.adder_checks}` | Selected adder native `drc`, `lvs`, `post['measurements']` plus the synthesis equivalence report, with the separate logic/state/transition counts. |
| `{evidence.width_checks}` | `results/adder_scaling.json: $.rows[*]`, fields n/state/passed/drc_clean/lvs_matched/pre_passed/post_passed/error, with `vector_plan`/`synthesis_equivalence` scope. Include incomplete rows. |
| `{evidence.load_checks}` | `results/full_add_load_sweep.json: $.rows[*]`, load_f/passed/unsettled/failures and `$.boundary`, `$.conditions`; include failing rows. |
| `{evidence.routing_checks}` | `build/pnr_fuzz/summary.json: $.completed`, `.passed`, `.failed`, `.inputs_stable`, `.cases[*]`; verify its fingerprint and each `fuzz.result.json` native evidence using `examples/fuzz_pnr.py`'s recorded method. No matching distributed summary means “unavailable”, not the historical count. |
| `{evidence.tests}` | A selected matching-revision JUnit XML, e.g. `build/sim_verification/pytest.xml`, via `xml.etree.ElementTree.parse(path)` and `testsuite` tests/failures/errors/skipped attributes, plus command, source revision and timestamp. Do not combine older stream totals into a supposed current full-suite count. `logs/review/pytest.xml` concerns the frozen review revision only. |
| `{evidence.colab_status}` | Matching real-Colab observation report, currently `docs/status/COLAB.md`, “Overall result”/“Environment and procedure”, with its tested source identity. `logs/colab/run-timing.json` records a failed old-tag run and manual follow-up; `printedFinalElapsedIncludesManualFollowup` forbids using that value as a successful benchmark. Until a matching successful run exists, render “No successful clean-Colab Run all recorded for this revision.” |
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
- STA, corner sweeps and the chip wrapper are optional. No unconditional
  result tokens or performance claims depend on them. If included, give each
  its actual report, conditions, state coverage and independent approval scope.
