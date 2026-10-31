# COLAB_RC5 — PASS, 2026-10-31

**Both immutable RC5 notebooks pass on their first fresh Colab CPU VM: 32/32 code cells each, CLI rc=0, no notebook exceptions.** English and Japanese ran in parallel on distinct VM endpoints. No retry or channel loss.

| Language | Execution including setup | Allocation + execution | Cell 6-6 / printed MPW step |
|---|---:|---:|---:|
| English | 787.419 s (13 min 7.4 s) | 791.555 s | 345.798 / 343.3 s |
| Japanese | 873.492 s (14 min 33.5 s) | 877.277 s | 384.554 / 381.4 s |

Notebook source: `fcdde92f161fb7f9107209ccdb590085b1f9ac1b`, byte-identical to `d7e5d0e`; implementation pin `7a33860d7a95393cfe88143a73e6365a8270088b`. GitHub originals, no overlay, upload or pin override. Both: **KLayout 0.30.6 / ngspice-42 / PDK 5d963db**. Organizer template: `b3dab389ddaac1056c93bf5704230c6d2f52d5b2`.

## Findings

- First circuit and dot4 pass **DRC 0 / LVS matched / post-layout SPICE** in both languages.
- Edited HDL: **31 cells**, all **81 logical inputs equivalent**, DRC 0 / LVS matched / SPICE PASS, maximum error **0.041834 V**. Analog coverage is **11/81 sampled states**, distinct from exhaustive logical equivalence.
- Scaling/power/timing cells c50/c52/c54 execute and display recorded N=2/4/8/16 data with `RECOMPUTE_SCALING=False`; the full campaign was not rerun.
- Live MPW c60 / 6-6 passes with **cache_hit=false**, unchanged **OSS_FRAME**, **16 actual pad/ESD instances**, **16 displayed pad rows**, GDS viewer and check table. Both print “all checks pass” / “全検査に合格”. Drawing DRC/LVS, mask DRC, organizer precheck, frame integrity, connectivity, metal/waiver policy and DC reserve checks pass. Japanese viewer/table labels verified.
- **RC4's precheck `pya` import failure is resolved.** Both organizer prechecks return 0. The notebook prepends the pinned KLayout target to `PYTHONPATH`; a fresh child Python imports the same `pya` as the kernel.
- Playground c63 / 7-1: **add2, 23 cells, 81 logical vectors equivalent, DRC 0 / LVS matched / SPICE PASS**, maximum error **0.043340 V**, 11/81 sampled transient states. All six rich outputs are present: schematic, 26-snapshot P&R replay, GDS, wire-C table, waveforms and summary. Cell times: **87.516 s English / 96.732 s Japanese**.

Saved rich output bodies and native result objects were audited. Shuttle and Playground overview images were visually inspected; previews are byte-identical between languages. Browser interaction was outside this CLI check. Signoff still records organizer allocation, final bond diagram and final CI as outstanding submission requirements.

## Interface requests

Update both editions' **6–8 minutes / 6〜8分** claim: these successful fresh-VM runs took **approximately 13–15 minutes including setup**. The MPW cell alone took approximately 5 min 46 s / 6 min 25 s on Colab, exceeding the approximately 90-second local estimate. No notebook or narrative edit was made by this stream.

## Decisions, validation and cleanup

Inspected saved exceptions as well as CLI rc because RC4 returned rc=0 despite a notebook exception. Measured allocation, full execution and cell 6-6 separately; post-run probes/shutdown are excluded from notebook time. Checked displayed GDS hashes against native artifacts, actual pad instances and visible Japanese labels. The only remote source-tree addition was the normal setup-generated `notebook/runtime.json`; no tracked implementation changes.

No notebook warning/stderr/exception outputs or CLI diagnostic warnings/errors. Exact CLI update notices are archived; CLI 0.7.4 was not upgraded. Both VMs explicitly terminated, and final server inventory is empty. Temporary full outputs, helpers, CLI state and copied credentials removed. No local packages installed, no code/narrative edits, no commits or pushes.

[Evidence, exact step lines, timings, warnings and reproduction](colab/v3-rc5-2026-10-31/README.md). Archive below 50 KB. Validation: actual Colab runs, all 64 completed cell events and unchanged source, required views/native checks, evidence JSON/links, shutdown and scope/whitespace checks. No owned pytest suite applies to this evidence-only brief.

Done: complete parallel qualification, output/native audit, evidence archive and cleanup. In progress: none. Blockers: none. Interface request: timing wording above. Completed before **2026-10-31 22:45 JST**; final timestamp and archive size are in [validation.json](colab/v3-rc5-2026-10-31/validation.json).
