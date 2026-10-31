# COLAB_RC4 — FAIL, stopped after required retry, 2026-10-31

**Release blocker reproduced on two fresh English Colab CPU VMs: cell c60 / 6-6 raises `PhysicalVerificationError` because the organizer MPW precheck cannot import `pya`.** No implementation, notebook or narrative repair was made; this stream owns evidence paths only. No commits or pushes.

| Run | CLI rc | Execution including setup | MPW cell / printed step |
|---|---:|---:|---:|
| English 1 | 0 despite notebook exception | 961.493 s (16 min 1.5 s) | 363.403 / 361.3 s |
| English 2, fresh retry | 1; repeated notebook exception, then channel loss | 2051.624 s (34 min 11.6 s) | 357.154 / 355.6 s |
| Japanese | Not run under the repeated-failure stop rule | — | — |

Source: notebook commit `948fda674798a122349c8e8aea0fc07e09986973`, byte-identical to `09fab61`; implementation pin `50f982bdc303494c5d0109f4fb797821fc64ee02`. Immutable GitHub originals, no overlay/upload/pin override. Both runs used KLayout 0.30.6, ngspice-42 and PDK 5d963db. Organizer template pin: `b3dab389ddaac1056c93bf5704230c6d2f52d5b2`.

## Findings

- First circuit and dot4 passed DRC 0 / LVS matched / extracted SPICE in both runs. Edited HDL passed with 31 cells, all 81 logical vectors equivalent, DRC 0, LVS matched, SPICE maximum error 0.042 V. Edited-HDL transient coverage is 11 sampled states, distinct from exhaustive logical equivalence.
- Scaling cells c50/c52/c54 completed with outputs. The first-run object audit confirms recorded N=2/4/8/16 data. This was not a rerun of the full scaling campaign.
- Live MPW: `force_signoff=True`, `cache_hit=false`; drawing DRC 0, drawing LVS matched, mask DRC 0, stock-frame geometry/text and connectivity clean, stock-waiver/metal policies clean, DC reserved margin met. **Organizer precheck rc=1 in both runs**, failing at `pre_check.py:18`, `import pya`, with `ModuleNotFoundError: No module named 'pya'`.
- The wrapper raises before `chip_view`, so the required “16 pads · all checks pass” line, shuttle viewer and pad table **do not appear**. Failed-artifact metadata contains OSS_FRAME and 16 pads; that does not satisfy the display requirement. Japanese labels remain unverified.
- Playground attempt 1 passed: `add2`, 23 cells, all 81 logical vectors equivalent, DRC 0 / LVS matched / SPICE PASS, maximum error 0.04334 V, 11/81 sampled transient states. All six requested rich outputs are present: schematic, P&R replay (26 snapshots), GDS, wire-C table, waveforms and summary. The embedded GDS overview was inspected. Browser interaction was outside this CLI test.
- Attempt 2 subsequently lost its channel during c63 / 7-1 with `RuntimeError: Connection was lost`. Its Playground printed synthesis/P&R/DRC/LVS/extraction passes, but no completed c63 event was saved; final SPICE and complete views are unverified. This is separate from the already-recorded second MPW failure.

## Diagnosis and interface requests

The kernel sees `pya` in `/content/tritflow-runtime/python-313-23d401dd51969032/pya/__init__.py`. The spawned `/usr/bin/python3` inherits `PYTHONPATH=/env/python`; its `sys.path` omits the pinned target, and `find_spec('pya')` returns None. Notebook setup inserts the target into the kernel's `sys.path`, while `tritflow/pnr/signoff.py::_run` launches the organizer precheck without propagating that path.

1. Make the precheck subprocess see the same pinned KLayout Python package, preserving environment isolation. Confirm a fresh subprocess can import `pya`, publish revised implementation/notebook pins, then rerun both languages on fresh VMs. No workaround was applied here.
2. Reassess the stated **6–8 minutes** after the fix. Attempt 1 processed all 32 cells in 16 minutes but failed; attempt 2's 34 minutes include waiting for a lost connection and are not a completed-run duration. Neither is evidence of successful end-to-end timing.

## Decisions, diagnostics and cleanup

The brief says to stop after a repeated failure. Two genuine c60 failures were captured before the later channel loss, so that stop condition took precedence over retrying the subsequent transport interruption. No third attempt or Japanese VM was created. This leaves Japanese qualification blocked, rather than passed or silently skipped.

CLI rc alone is insufficient: attempt 1 returned 0 with one notebook exception. Attempt 1 saved all 32 cell events; attempt 2 saved 31. No notebook warning/stderr outputs were captured. Notebook/precheck tracebacks, the channel-loss frames, exact CLI update notices and a recovered local output-trimming helper error are archived. Two temporary helper artifacts were briefly written outside the evidence directory and immediately moved into it; no pre-existing file was changed and no stray artifact remains. See the harness note.

English VM 1 was explicitly terminated. VM 2 was already absent when stop was requested; final server inventory reports **no active sessions**. Local CLI state, temporary originals/full outputs, helpers and copied credentials were removed. No local packages installed. A stale progress label is not a stage timer: the first run's MPW step was 361.3 s, but its full-chip MDP was only 5.191 s.

[Evidence and reproduction details](colab/v3-rc4-2026-10-31/README.md). The retained archive is below 50 KB. Reproduction: fetch the immutable source URL, `colab new -s NAME`, `colab exec -s NAME -f ORIGINAL.ipynb --timeout 1200`, audit saved error outputs as well as rc, then `colab stop -s NAME`. This run isolated CLI state/history/settings under the permitted evidence directory.

Done: two fresh English runs, required retry, failure diagnosis, output audit, evidence archive and VM cleanup. In progress: none. Blockers: subprocess `pya` import; Japanese and complete shuttle-view qualification require a new fixed RC. Interface requests: the two above. Tests: actual Colab runs and artifact/cleanup validation; no owned pytest suite applies to these evidence-only changes.

Final validation completed **2026-10-31 20:09 JST**, before the 21:00 JST reporting deadline: source hashes, all evidence JSON, captured-cell counts, repeated precheck failure, first-run Playground outputs, Markdown links and server cleanup checked. Temporary work directory is absent; retained archive totals **39,978 bytes**. `git diff --check` reports no whitespace errors for the owned paths.
