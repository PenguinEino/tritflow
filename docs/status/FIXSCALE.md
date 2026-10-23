# FIXSCALE status

Implementation and GDS proof complete. The full-suite acceptance gate remains
blocked by two notebook-regeneration failures outside FIXSCALE's ownership,
in addition to the two explicitly allowed stale-payload failures.

## Scope and decisions — 2026-10-24

- Read `AGENTS.md`, `docs/concept.md`, `docs/interfaces.md`, and
  `briefs/FIXSCALE.md`. Work stays in the brief's paths; no commit or push.
- Restore `tritflow/pnr/chip_power.py` directly from `git show 0fd73b0~1:...`,
  without changing Git state. Required SHA-256:
  `a3f4b62fa2d91ba5408071cdb5786f30cf2ef96401ba6d62f192737efe262a8c`.
- Keep the stock-frame distribution calculation in `chip_frame_power.py`.
  Preserve the prior width/reserve equations, geometry, TC ordering, and
  input checks. The frame still uses the unchanged `_via_array` helper.
  Copying the distribution portion avoids building then discarding legacy
  TEG feeders or depending on incidental list boundaries in `_power_header`.
- Reuse the exact archived seed-0 dot4 macro. Rebuild only its stock-frame
  wrapper in `tests/` and compare drawing/mask bytes and the power model.
  Keep `results/dot_scaling.json` and all published chip artifacts unchanged.
- Update current source hashes in provenance after the rebuild. Original
  qualification hashes describe the unchanged archived evidence and will
  remain historical, with that distinction recorded explicitly.
- Use the pinned public PDK and the locally qualified Ubuntu ngspice-42
  wrapper selected by the existing simulator resolver. No packages installed.

## Done

- Restored the required `chip_power.py` SHA-256.
- Compared the complete stock power data and header against the pre-fix
  implementation on the archived dot4 macro: exact equality.
- Added a native regression that rebuilds the frame and compares the drawing,
  distribution header, and all power rails/straps/vias/pins with the recorded
  artifacts; the source macro must remain byte-identical. The native MDP deck
  timestamps its mask, so mask comparison disables GDS timestamps first.
- Rebuilt the stock-frame top from the archived macro. Drawing SHA-256 remains
  `6d2453708f58a442dbf151d4afe6bb77d4c9f3e1b813807a781c6068a592f6dd`.
  Timestamp-normalized mask and full power geometry/header also match exactly.
- Fresh native drawing/mask DRC: zero violations each; strict drawing LVS:
  matched; stock-frame policy: clean; worst DC utilization: 0.7480360683534744
  (25.1964% reserve). Native qualification took 49.48 s. This reruns the default
  fixed-die/frame precheck; the archived organizer-template precheck is retained.
- Updated provenance's current source hashes and added a separate rebuild
  verification record. Original qualification-input hashes are explicitly
  historical. Verified every published artifact hash, including both canonical
  GDS files and `evidence.zip`, is unchanged; scaling JSON is byte-identical to
  HEAD.
- All nine `tests/test_scale_views.py` tests passed, including both previously
  failing recorded-data readers.
- Final focused run: **12 passed in 0.52 s** for `tests/test_scale_views.py`
  and `tests/reuse/test_snapshot.py`, including the refreshed VISFIX source
  hash. The new native frame regression passed in the full suite, as did all
  other PNR tests.

## In progress

None within the FIXSCALE-owned implementation. All test scratch files stayed
in `tests/build/fixscale/`; a local plugin overrode the submission conftest's
temporary-directory setting.

## Blockers

- `notebook/tests/test_document.py::test_notebook_chapters_code_and_generator_reproducibility[en]`
  and `[ja]` still fail in a fresh process. Both saved notebooks differ from
  their current generator in markdown cells `c0`, `c35`, and `c63`: the new
  introductory lead/flow figure, routing retry description, and references.
  This appeared as other streams committed narrative changes during the run
  (HEAD advanced from `150c4de` to `36d2e68`). These are **not accepted failures**.
- The brief forbids editing `notebook/v3/` or narrative/generator files. The
  integrator must regenerate both source notebooks with the existing source
  pin `cc9a49e97e1ad098743494db7d82adb34a379bbe`, then rerun the two document
  tests. Generated comparison copies already exist under
  `tests/build/fixscale/refresh/test_notebook_chapters_code_an{0,1}/`.
- Expected/allowed pending work remains the submission payload rebuild. Its
  two tests fail because the English source notebook changed since capture.

## Interface requests

- VISFIX changed `notebook/reuse.py` during the full suite, despite its status
  file's stated deferral until FIXSCALE exited. This caused the snapshot source
  hash test to fail. Inspected the diff: only localization/display labels
  changed; HDL, simulation and physical artifact generation are unchanged.
  Refreshed that file's current source hash in the FIXSCALE-owned provenance
  only, with an explicit scope note. VISFIX must refresh it again if further
  edits occur. Do not replace historical qualification or published hashes.
- The submission payload is outside this stream's ownership.
- Regenerate the bilingual notebooks before accepting the full-suite gate;
  no notebook generator, narrative, payload, or unowned implementation file
  was modified by FIXSCALE. No test was weakened or skipped by this stream.

## Validation

The first native regression run passed all native checks and the byte-exact
drawing comparison, then exposed the mask deck's timestamp difference. After
disabling those timestamps, the mask and remaining power comparisons passed.
The preliminary full-suite run was interrupted to load that corrected test.

- Required full suite: **944 passed, 8 failed, 2 skipped in 1218.59 s**
  (954 tests). All physical, scaling and frame tests passed. The failures were
  one VISFIX source-hash race, two stale generated notebooks, three submission
  template/import races during concurrent edits, and the two allowed stale
  payload checks.
- Fresh-process rerun of `tests/test_scale_views.py`,
  `tests/reuse/test_snapshot.py`, `notebook/tests`, and `submission`:
  **60 passed, 4 failed in 10.54 s**. The hash fix passed, and all three
  submission-template races disappeared with fresh imports. Only the two
  notebook reproducibility failures and the two allowed payload failures
  remain; see Blockers. This is not a claim that the full-suite gate passed.
- Final focused source/scaling/snapshot check: **12 passed in 0.52 s**.
- The full suite's two existing conditional skips were
  `tests/sta/test_propagation.py::test_real_default_midpoint_report_and_source_pattern`
  and `tests/sta/test_sta_timing.py::test_real_published_cells_and_six_trit_adder`.
- Final SHA checks confirm exact historical `chip_power.py`, unchanged
  `results/dot_scaling.json` relative to starting commit `150c4de`, and every
  published chip artifact/source hash matching provenance. `git diff --check`
  passes for all FIXSCALE changes. No packages installed; no commit or push.

### Commands and local evidence

```bash
export PYTHONDONTWRITEBYTECODE=1
export TR1UM_PDK=/home/ishi-kai/pdk/TR-1um-pinned
export NGSPICE_BINARY=/home/ishi-kai/.local/opt/tritflow-ubuntu-24.04/bin/ngspice
export TMPDIR="$PWD/tests/build/fixscale/tmp"
python3 -m pytest -q tests/test_scale_views.py \
  tests/pnr/test_chip_frame.py::test_stock_chip_rebuild_preserves_recorded_geometry \
  -p no:cacheprovider --basetemp=tests/build/fixscale/rebuild
PYTHONPATH="$PWD/tests/build/fixscale:$PYTHONPATH" \
  python3 -m pytest -q tests notebook/tests submission \
  -p isolate_pytest -p no:cacheprovider
```

`tests/build/fixscale/isolate_pytest.py` is a local, ignored pytest plugin that
overrides the submission conftest's `basetemp`/`TMPDIR` at session start and
resets `TMPDIR` after collection. It changes only temporary-file placement,
without filtering tests or changing fixtures/assertions. The ordinary full
suite command remains `python3 -m pytest -q tests notebook/tests submission`.

Local logs: `tests/build/fixscale/rebuild.log` and
`tests/build/fixscale/full-suite.log`; follow-up logs:
`tests/build/fixscale/refresh.log`, `tests/build/fixscale/final-focused.log`.
The fresh-process rerun used the same plugin with
`FIXSCALE_TEST_BASE=refresh` to preserve the original native evidence.
Native rebuild report:
`tests/build/fixscale/rebuild/test_stock_chip_rebuild_preser0/chip/signoff/signoff.summary.json`.
Provenance records that report's SHA-256 separately from the original archive.
