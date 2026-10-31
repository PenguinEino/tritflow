# v3 RC4 check, fresh Colab VMs (CLI), 2026-10-31

**FAIL: cell `c60` / `6-6` fails on both fresh English VMs.** The organizer MPW precheck subprocess cannot import `pya`. Japanese was not run because the brief requires stopping after a repeated failure. English attempt 2 subsequently lost its CLI channel in the Playground; that separate interruption does not explain either earlier precheck failure.

Source: branch `notebook-v3`, notebook commit `948fda674798a122349c8e8aea0fc07e09986973`, implementation pin `50f982bdc303494c5d0109f4fb797821fc64ee02`. Both original notebooks were fetched from immutable GitHub URLs and byte-compared with their git objects and `09fab61`. No overlay, upload, pin override or notebook modification. [URLs and hashes](source.json).

| Run | CLI rc | Execution including setup | Allocation | MPW cell / printed step |
|---|---:|---:|---:|---:|
| English 1 | 0, but notebook FAIL | 961.493 s (16 min 1.5 s) | 10.191 s | 363.403 / 361.3 s |
| English 2, fresh retry | 1, notebook FAIL plus channel loss | 2051.624 s (34 min 11.6 s) | 3.775 s | 357.154 / 355.6 s |
| Japanese | Not run | — | — | — |

Timing surrounds `colab exec`; allocation, post-run audit and shutdown are separate. MPW cell time is the interval between completed CLI history events, including template clone and cell overhead; the printed step measures the wrapper build/signoff call. Attempt 1 processed all 32 code cells, with one exception. Attempt 2 captured 31 completed cell events, with the same exception, then lost the channel during c63; its elapsed time includes waiting for the lost connection and is **not a completed notebook duration**. Allocation plus execution: 971.684 s and 2055.399 s. Neither run supplies a successful full-notebook timing. The stated **6–8 minutes is unsupported** by this RC; update it after repairing and rerunning both languages.

Both runs: **KLayout 0.30.6, ngspice-42, PDK 5d963db**. First circuit and dot4: **DRC 0 / LVS matched / extracted SPICE pass**. Edited HDL: **31 cells / 81 exhaustive logical vectors / DRC 0 / LVS matched / SPICE PASS / maximum error 0.042 V**. Scaling c50, power c52 and timing c54 completed with output; the first run's object audit confirms N=2/4/8/16. These scaling data are recorded evidence, not a newly rerun scaling campaign.

The live MPW call cloned the organizer template pinned to `b3dab389ddaac1056c93bf5704230c6d2f52d5b2` and ran with `force_signoff=True`; both reports say `cache_hit=false`. Both have drawing DRC 0, drawing LVS matched, mask DRC 0, clean stock-frame geometry/text, connectivity and stock-waiver/metal checks, and the reserved DC current margin met. Both fail only the organizer precheck (rc=1):

```text
File ".../mpw_template/scripts/pre_check.py", line 18, in <module>
  import pya
ModuleNotFoundError: No module named 'pya'
```

Notebook `to_chip()` consequently raises `PhysicalVerificationError`. **No “16 pads · all checks pass” step, shuttle viewer or displayed pad table appears.** Failed-artifact metadata confirms OSS_FRAME and 16 pads; that is not a display pass. Japanese labels remain unverified. Signoff itself took 204.123 s / 200.831 s, within the longer wrapper step. A lingering `run_mdp.drc` progress label was not a stage timer: first-run full-chip MDP actually took 5.191 s.

Diagnosis confirmed on VM 1: the kernel finds `pya` under `/content/tritflow-runtime/python-313-23d401dd51969032`, but the spawned `/usr/bin/python3` sees `PYTHONPATH=/env/python`, lacks that target in `sys.path`, and finds no `pya`. The precheck runner inherits the environment, not the kernel's modified `sys.path`. Make the precheck subprocess see the pinned KLayout Python package, then publish new pins and requalify. No repair was applied in this evidence-only stream.

**Playground, attempt 1: PASS.** `add2`: 23 cells, all 81 logical vectors equivalent, DRC 0 / LVS matched / SPICE PASS, maximum error 0.04334 V, 11 of 81 input states sampled. Schematic, 26-snapshot P&R replay, downloadable GDS, wire-capacitance table, waveforms and summary are present in saved rich outputs. The embedded GDS overview was visually inspected. Browser interaction was not tested. Attempt 2 printed Playground synthesis/P&R/DRC/LVS/extraction passes but lost the channel before its cell outputs were committed; its final SPICE and complete views are unverified.

No notebook warning/stderr outputs were captured. Each run has the c60 exception and the precheck traceback above; attempt 2 additionally reports `RuntimeError: Connection was lost`. Exact CLI update notices and the recovered local trimming-helper error are retained. Because two genuine notebook failures had already been captured before the channel loss, the repeated-failure **stop** condition took precedence over retrying that later transport failure; no third VM or Japanese VM was created.

English VM 1 was explicitly terminated. VM 2 was already absent when `colab stop` was issued; final server inventory reports **no active sessions**. [Cleanup](cleanup.txt). Temporary originals, full outputs, helper scripts, local CLI state and copied credentials were removed after audit. Retained archive is below 50 KB; no local packages installed, code/narrative edits, commits or pushes.

Evidence: [English 1 steps](en-1-exec.txt), [result](en-1-result.json), [output audit](en-1-audit.json), [chapter 6/7 tables](en-1-chapter6-7.txt), [views](en-1-views.json), [diagnosis](en-1-diagnostic.json), [traceback](en-1-traceback.txt), [precheck](en-1-mpw-precheck.txt), [notices](en-1-warnings.txt); [English 2 steps](en-2-exec.txt), [result](en-2-result.json), [output audit](en-2-audit.json), [tables](en-2-chapter6-7.txt), [signoff](en-2-diagnostic.json), [traceback](en-2-traceback.txt), [precheck](en-2-mpw-precheck.txt), [channel loss](en-2-channel-drop.txt), [notices](en-2-warnings.txt); [harness note](harness-notes.txt), [stream report](../../COLAB_RC4.md).
