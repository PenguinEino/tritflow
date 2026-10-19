# PIN — ngspice 42 evidence and dependency qualification complete

2026-10-19. The user direction change and simulation-server instructions in `briefs/PIN.md` are the delivered design. Earlier ngspice-46 builds/experiments are superseded.

## Result

- Authoritative evidence regenerated on `penguin@einosuke-llm-5090` (`strata-ubuntu`, Ubuntu 24.04.5 amd64), using official Ubuntu `ngspice=42+ds-3build1` and native KLayout **0.30.6**. Source/data and native build evidence were returned. All 2,389 selected return-file hashes verified; this count includes disposable retained row caches.
- All requested campaigns completed: sizing, eight characterizations, 160 primary cell timing points, 30 poly-R profiles plus matched-step controls, 175 STA propagation points, resolution controls, four post-layout examples, refined output-load boundary, N=1…6 scaling, 54 T/V cases, delay/rail/internal-path/charge diagnoses, publication audit, all nine figures and portable paper evidence.
- Publication audit passes. STA has **10 qualified/current designs and 39 outputs**. All saved nominal functional cases pass. The existing matched-event accuracy result remains **38/39 within 20%**; the static envelope covers the saved nominal cases. These finite datasets are not a PVT or arbitrary-waveform guarantee.
- The final source snapshot passed five full notebook executions, each **35/35 cells**: server, three local Python boundaries, and real Colab. Earlier setup-inclusive and reader-correction Colab passes are also retained. Final notebook SHA-256 is `7e4ce664606f116103dd959c6ceb3857f281a45392dba5a5ff749a6c52074a62`.
- No commit, push, release or remote-service action was performed. The simulation server is no longer needed. Workspace/runtime files remain under `~/tritflow-sim` for audit. The first setup populated pip's default user cache before cache isolation was corrected; no pre-existing cache files were removed.

## Exact runtime

- Ubuntu snapshot: `20261019T000000Z`. Official ngspice closure: 38 exact packages per amd64/arm64 lock; combined amd64 KLayout/ngspice closure: 197 packages, plus the checksum-pinned official KLayout .deb. Every URL/version/SHA is recorded. Native tools are privately unpacked with the locked loader and libraries; no native tool is compiled or bundled.
- Private unpacking is intentional: this VM has no passwordless sudo, and replacing Colab's live libc/Qt/Ruby/Python is unnecessary. All callers use explicit runtime configuration. Setup no longer creates `~/bin/klayout` outside its prefix.
- ngspice ELF SHA-256 (server **and real Colab**): `820658317b0b54035208da41936fd6871ce924036e5ea4113a4168b821b7fc45`. Official arm64 ELF: `6b2ecd9b08694b010420f0eeea6591f85466f322dbd2e0bfb759d53d269cd957`. Wrapper identity is also hashed, so prefix/library-path changes invalidate caches. Runtime rejects other ngspice releases. PATH never silently selects the old development simulator.
- Kept the explicit **DC + PWL** source fix required by ngspice 42. Kept binary-identity keys in inner and outer waveform/corner/scaling/load/STA caches.
- `spinit` text relocates official codemodel paths; the ELF and .cm bytes remain official. The clean server exposed a missing private PulseAudio library search directory; it is fixed. Final server/Colab loader audits resolve all 33 ngspice and 114 KLayout dependency entries inside the locked root.
- Hash-locked Python wheels, no committed wheels: local complete lock, lower boundary, observed Colab host, evidence producer and private Colab target. The evidence producer retained NumPy 2.4.3/SciPy 1.17.1/Matplotlib 3.10.8/Plotly 7.1.0 to avoid also migrating that scientific stack. The notebook locks use their separately tested versions.
- Fresh Colab preload inventory: Python 3.13.16; NumPy 2.1.3, Matplotlib 3.10.0, Pillow 11.3.0, IPython 7.34.0, ipywidgets 7.7.1, cycler 0.12.1, dateutil 2.9.0.post0, kiwisolver 1.5.1, packaging 26.3, pyparsing 3.3.3. Loaded host modules are preserved. Unloaded SciPy 1.16.3/Plotly 5.24.1/KLayout/Lark and dependencies install privately with `--no-deps --require-hashes`.
- Font metrics are pinned too: official `fonts-urw-base35=20200910-8`, package SHA plus four Nimbus Roman OTF hashes in `notebook/fonts-lock.json`. Data-only private unpacking; no font package scripts run. Font registration replaces host Nimbus candidates in memory. All four files equal the original VM's fonts; the synthesis figure's 0.6 em padding assertion passes unchanged. No fonts are bundled.
- `notebook/Dockerfile` pins the base digest and exact snapshot bootstrap packages. `.github/workflows/notebook-pinned.yml` builds/runs it weekly, with a pinned checkout action. Docker is unavailable on the VM/server, so no Docker image build is claimed here. The full Docker Python lock was tested natively on amd64; local Python-boundary tests retain this VM's native KLayout 0.30.9. Authoritative native KLayout 0.30.6 is tested on the server and Colab.

## Every changed number against HEAD

Baseline: immutable `839adbf19f7590221d18d171adaaddb95c8fd27a`, captured through `git show`/`git cat-file`; interrupted working-tree values were never the numerical baseline.

- Complete ledger: [`notebook/assets/ngspice42_changes.json.gz`](../../notebook/assets/ngspice42_changes.json.gz).
- Compact index: [`notebook/assets/ngspice42_summary.json`](../../notebook/assets/ngspice42_summary.json).
- **1,083 baseline JSON records**, **450 changed records**, **197,158 changed scalar/status entries**, no missing baseline records. Each entry has file, JSON path, before, after and delta. Added/removed metrics and list tails are retained. The count includes duplicated published representations of measurements.
- Adaptive transient arrays are not paired by sample index. The ledger compares every reported endpoint/settling/current/capacitance/timing-arc metric and fixed-grid DC sizing sample. Runtime durations, hashes and generation metadata are excluded. Native waveforms/decks/logs are retained in `build/` and the four-design ZIP.
- Two additional working-tree DC-bias records are explicitly identified as additions (no HEAD counterpart); they were preserved from the other stream. They account for 15,083 newly recorded scalar entries.
- No existing finite measurement became null, and no null measurement became finite. The only pass/complete changes are two historical Phase-4 flags improving false→true. Cache-reuse metadata changes are also visible.
- This is a total regeneration comparison: HEAD used arm64/development ngspice and native KLayout 0.30.9; the authoritative run uses amd64/package ngspice 42 and KLayout 0.30.6. Do not attribute every last-bit difference to ngspice alone.

| Carry fit | HEAD (ns/trit) | New (ns/trit) | Delta (ns/trit) |
|---|---:|---:|---:|
| Devices only | 48.9524653632 | 48.980882459 | +0.0284170957729 |
| Devices + wire C | 56.8813930713 | 56.8809080387 | -0.000485032597204 |

The measured 500 ns full-adder load bracket is unchanged: **12.8125 pF PASS / 12.96875 pF FAIL**. INV sizing remains **76/90 PASS**, NANY **17/18 PASS**.

| Characterization | HEAD max settling (ns) | New (ns) | Delta (ps) |
|---|---:|---:|---:|
| INV | 37.7174544364 | 37.7170794207 | -0.37501568354 |
| NAND | 40.7667397438 | 40.7621959881 | -4.54375565214 |
| NOR | 49.4862254326 | 49.4889526686 | +2.72723609206 |
| NANY | 50.8878091562 | 50.8914600194 | +3.65086315146 |
| BUF | 39.2039849165 | 39.2010160073 | -2.96890913192 |
| TIEP | 0 | 0 | +0 |
| TIEZ | 0 | 0 | +0 |
| TIEN | 0 | 0 | +0 |

The largest finite settling change in the T/V summaries is full_add at 27 °C, ±5.5 V against the fixed nominal band: −12.1949333415 ns. Its full before/after context is in the ledger. NAND's poly proxy also has a 1e−11 Ω text-rounding difference in one resistor; GDS and intrinsic cell devices are unchanged.

## Notebook qualification

| Run | Kernel Python | Cells | Seconds |
|---|---|---:|---:|
| Authoritative server; forced fresh four-design campaign | 3.12.3 | 35/35 | 348.124 |
| Minimum scientific stack | 3.12.12 | 35/35 | 64.236 |
| Observed Colab scientific stack | 3.13.16 | 35/35 | 63.314 |
| Docker Python lock boundary | 3.12.12 | 35/35 | 62.413 |
| Real Colab, setup-inclusive earlier snapshot | 3.13.16 | 35/35 | 307.770 |
| Real Colab, latest notebook/archive | 3.13.16 | 35/35 | 313.806 |

The latest server/boundary rows and latest Colab row qualify the final notebook SHA above; the setup-inclusive row records the earlier e04341e snapshot.

Reports and executed notebooks are under `build/pin42/notebook-*`; real-Colab reports are `colab-final-report.json` and `colab-latest-report.json`. Full per-cell results and empty traceback lists are recorded in `docs/status/COLABMCP.md`. Source/PDK/options/native hashes validate the portable four-design ZIP; it retains 54 native evidence files. The three local boundaries explicitly reused that labelled recorded campaign. The server forced fresh physical/electrical runs.

The real-Colab check uses a fresh kernel in the existing Ubuntu 24.04.5 VM. Setup-inclusive pass removed runtime.json and executed the real Colab installer. The qualification adapter relaxes only the dirty-checkout guard for the transferred uncommitted patch; origin, full commit, runtime marker and version checks remain active. This is working-tree qualification, not immutable-release proof. The last concurrent frontend changes altered learning.py, methods.py, stages.py and the generated notebook. The source fingerprint correctly invalidated the old archive. The four-design archive and all five qualifications were refreshed against the latest snapshot; the completed full sizing/timing/scaling/corner campaigns were retained.

Final Fig. 2: ten DC sweeps and rendered-PNG inspection pass. For each gate, `min over B-pairs(max over A |ΔY|)` is NAND 4.898209089107485 V, NOR 4.990533432519134 V, NANY 5.118287635735347 V. NAND at A=+5 V gives +4.999998867389579 / −0.1026365050847957 / −4.999999402298856 V. Image and checks: `build/pin42/colab-fig2-final.{png,json}`. Colab only used the authorised local-MCP connection dialog; no sign-in/OAuth/Save/Share. All temporary runner cells were deleted and only the original empty scratch cell remains.

## Fixes found during the run

1. Clean-server loader isolation exposed PulseAudio's nested library path; fixed before accepting evidence.
2. The optional schematic delay-control solve hit a nonphysical off-rail initial root under ngspice 42. Its four controls now use identical ideal internal-logic soft `.nodeset` guesses, with schematic reversible names or LVS mappings. No `.ic`, `uic`, transient forcing or changed devices. The protocol and every seed are recorded. Original failed deck/log retained in `build/pin42/diagnose-initial/`.
3. Figure generation needs the original NANY GDS. Copied it read-only into the remote workspace and verified SHA `3403d325575c08cee2765c459d40985ee041db48a1ed21f1e13f3d9306af6282`. A launcher points Fig. 4 at this copy; no figure source changed. Pinned Nimbus metrics fix the clean-server label-padding failure.
4. The first server notebook saw a new waveform_scope import with an older remote VIZ copy. Synced the concurrently updated notebook/VIZ helpers together, then ran the successful fresh kernel. Initial failure report is retained.
5. The original unanchored rsync build exclusion also omitted ignored historical baseline summaries under results/dev_before_pinned/build. Restored the 120 KB archive and regenerated reader reports. Publication now rejects missing historical data instead of silently emitting null before-values. Future source syncs must anchor the ignored-root exclusion (`/build/`). These historical summaries are local ignored data; preserve or deliberately package them for producer reproduction. Their original omission is now rejected explicitly rather than converted to a null comparison.
6. STA incorrectly required a Git checkout ID for the checksum-verified PDK tarball. It now accepts archive provenance only when every consumed deck/model hash equals the pinned cell-publication reference; mismatches still fail. All 10 designs/39 outputs now qualify. Only readers/statistics/figures were refreshed; accepted SPICE campaigns were not repeated.

## Tests and remaining integration work

- Core suites: **149 passed** (`tests/sim tests/sta tests/cells tests/extract`, 476.51 s).
- Added baseline/archive provenance regressions pass; focused robustness **7 passed**, STA **36 passed**. The broader tree had **511 passed / 2 stale editorial assertions failed** (158.15 s); both editorial failures were rechecked against the final source (0.33 s) and remain. Counting the two new regressions gives 662 passing cases and two outstanding editorial cases.
- Final focused reader checks: **50 passed** (19.95 s). Setup/bootstrap/cache/font/runtime focused checks pass. No local Python package was added during this continuation; existing hashed uv boundary venvs were reused. Native/font .debs install privately.
- Reproduce focused checks: `PYTHONPATH=notebook:. python3 -m pytest tests/sta tests/sim/test_robustness.py notebook/tests/test_publications.py notebook/tests/test_pin_changes.py -q`.
- Full broader command: `python3 -m pytest tests notebook/tests -q`. The two ownership/interface requests below remain; this is not a claim that the whole tree is green.

### Interface requests (integrator / FRONTEND / editorial owners)

1. `notebook/tests/test_document.py::test_colab_note_matches_the_latest_published_verification`: colab_verified.json still names historical commit `0ffe7a12c34738664e9e788853d87edc9da5b7ec`, 300.7 s, but its report path docs/status/COLAB.md was replaced with round 13 at 839adbf. Restore a matching historical report or publish coherent release evidence after the immutable release test. Do not label this uncommitted PIN patch as verification of the old commit.
2. `notebook/tests/test_editorial.py::test_static_context_and_embedded_figures_have_no_unresolved_results`: still requires `render_gds(custom_lay.gds_path...)` after the concurrent VIS change to `gds_viewer(...)`. Update the owner test to the intended new viewer contract. Both new viewer code and all notebook cells passed real Colab and the boundaries.
3. Regenerate SOURCE_REF after the implementation commit exists. Use a full 40-character SHA in executable bootstrap; annotated tags `isscc2027-v1.0.0`, `v1.0.1`, etc. are descriptive and must never move. Update launch badges/links to the final immutable release. Regenerate submission after that commit and run the unpatched immutable-source Colab check before release. No commit/push was authorised here.
4. The generator's hard-coded Appendix recovery paragraph still describes a colab-v0 shallow clone and preserving all four scientific packages. Proposed replacement (narrative remains integrator-owned):

> Setup downloads checksum-verified KLayout 0.30.6 and Ubuntu ngspice 42+ds-3build1 with exact snapshot dependencies. Hash-locked unloaded Python packages and pinned circuit-label fonts install privately; Colab's imported scientific modules are preserved. Tested minimum/current stacks and weekly checks cover the review period. The digest-pinned Docker environment provides an independent reproduction route. The executable source reference is a full immutable Git commit.

No unfinished PIN simulation or qualification remains. The two editorial tests and final immutable release/payload are integration work; their files/prose were left to their owners under docs/interfaces.md.
