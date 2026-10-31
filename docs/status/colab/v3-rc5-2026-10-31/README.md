# v3 RC5 check, fresh Colab VMs (CLI), 2026-10-31

**PASS in both languages on the first attempt: 32/32 code cells, CLI rc=0, no notebook exceptions.** English and Japanese ran concurrently on distinct fresh CPU VMs. No retry or channel loss.

Source: branch `notebook-v3`, notebook commit `fcdde92f161fb7f9107209ccdb590085b1f9ac1b`, implementation pin `7a33860d7a95393cfe88143a73e6365a8270088b`. Original notebook bytes from immutable GitHub URLs match their git objects and `d7e5d0e`. No overlay, upload, source edit or pin override. [URLs and hashes](source.json).

| Language | CLI rc | Execution including setup | VM allocation | Cell 6-6 / printed MPW step | Playground cell |
|---|---:|---:|---:|---:|---:|
| English | 0 | 787.419 s (13 min 7.4 s) | 4.136 s | 345.798 / 343.3 s | 87.516 s |
| Japanese | 0 | 873.492 s (14 min 33.5 s) | 3.785 s | 384.554 / 381.4 s | 96.732 s |

Allocation plus execution: **791.555 s English, 877.277 s Japanese**. Execution surrounds `colab exec`, including setup, connection and output-save overhead; post-run inspection and shutdown are separate. Cell 6-6 time is the interval between completed CLI history events, including template clone and display overhead; its printed step measures the build/signoff call. English execution ended at 20:24:57 JST and Japanese at 20:26:23 JST.

**Update “6–8 minutes” / “6〜8分” to reflect approximately 13–15 minutes including setup.** This is an observed range on two fresh Colab CPU VMs, not a guarantee. The approximately 90-second local MPW estimate also understates the Colab cell times of 5 min 46 s / 6 min 25 s.

Both: **KLayout 0.30.6, ngspice-42**, PDK `5d963db9d44e192d37a0489c208bfccf2e2f690c`, organizer template `b3dab389ddaac1056c93bf5704230c6d2f52d5b2`.

## Required checks

- First circuit and dot4: **DRC 0 / LVS matched / post-layout SPICE pass**, both languages.
- Edited HDL `dot4_fixed`: **31 cells**, exhaustive logical equivalence over **81 inputs**, DRC 0, LVS matched, SPICE PASS, maximum error **0.041834 V**. Transient simulation samples **11/81 states**, separately from exhaustive logical equivalence.
- Scaling c50, power c52 and timing c54 completed with outputs. N=2/4/8/16 recorded data were displayed with `RECOMPUTE_SCALING=False`; the full campaign was not rerun. The recorded optional N=32 routing failure remains an explicitly excluded historical attempt.
- Live MPW c60 / 6-6: `force_signoff=True`, **cache_hit=false**, unchanged **OSS_FRAME**, **16 actual pad/ESD instances** and **16 displayed rows P01–P16**. Drawing DRC 0, drawing LVS matched, mask DRC 0, organizer precheck rc=0; frame geometry/text, connectivity, stock-waiver policy, metal preservation and DC reserve checks pass. Both viewer downloads match the audited live GDS hash.
- Japanese chip labels appear in visible output text: **全体表示**, **座標の単位：µm**, **検査**, **信号 / 電源**, **方向**, **電源**, **入力**, **出力**. The GDS viewer, check table and pad table all appear.
- Playground c63 / 7-1 `add2`: **23 cells**, all **81 logical inputs equivalent**, DRC 0, LVS matched, SPICE PASS, maximum error **0.043340 V**, **11/81 sampled transient states**. All six rich outputs appear in both languages: **schematic, P&R replay (26 snapshots), GDS, wire-capacitance table, waveforms and summary**.

Exact MPW step lines:

```text
✓ Place in the MPW frame and verify 2500 × 2500 µm · 16 pads · all checks pass 343.3s
✓ MPWフレームに載せて検証 2500 × 2500 µm · パッド16個 · 全検査に合格 381.4s
```

**RC4's `pya` blocker is resolved in these runs.** `PYTHONPATH` starts with `/content/tritflow-runtime/python-313-23d401dd51969032`; child `/usr/bin/python3` imports the same `pya` as the kernel. Both actual organizer precheck logs confirm successful top name, database unit, die area and required frame checks. Signoff itself took 191.346 s / 213.767 s within the longer MPW cell; a lingering progress label is not a stage timer.

Saved rich output bodies and native result objects were audited. Shuttle and Playground overview images were visually inspected; English/Japanese previews are byte-identical by SHA-256. Browser interaction was outside this CLI procedure. Full-chip `submission_ready` remains false for organizer slot allocation, final bond diagram and final CI requirements; notebook/physical checks pass.

## Warnings, reproduction and cleanup

**No notebook warning lines, stderr outputs, exceptions, or CLI diagnostic WARNING/ERROR/CRITICAL records.** The CLI advertised 0.7.5 while running 0.7.4; every occurrence is retained with its command in warning files and cleanup. No CLI update or local package installation.

For each language: fetch its original URL in `source.json`; run `colab new -s NAME`, `colab exec -s NAME -f ORIGINAL.ipynb --timeout 1200`, audit saved exceptions as well as rc, then `colab stop -s NAME`. Run the two languages in parallel. A local launcher scoped CLI credentials/state/history/settings/logs to the temporary evidence directory without changing notebook code or remote execution behavior. Read-only post-run probes checked native results. The only untracked remote source-tree file was the normal setup-generated `notebook/runtime.json`; tracked implementation files were unchanged.

Both VMs explicitly terminated (stop rc=0); final server inventory reports **no active sessions**. Temporary originals, full outputs, images, helpers, CLI state and copied credentials removed after audit. Retained archive below 50 KB. No implementation/narrative edits, commits or pushes.

Evidence: [English steps](en-1-exec.txt), [timing](en-1-result.json), [cell audit](en-1-audit.json), [tables](en-1-chapter6-7.txt), [views](en-1-views.json), [native results](en-1-diagnostic.json), [precheck](en-1-mpw-precheck.txt), [notices](en-1-warnings.txt); [Japanese steps](ja-1-exec.txt), [timing](ja-1-result.json), [cell audit](ja-1-audit.json), [tables](ja-1-chapter6-7.txt), [views](ja-1-views.json), [native results](ja-1-diagnostic.json), [precheck](ja-1-mpw-precheck.txt), [notices](ja-1-warnings.txt); [cleanup](cleanup.txt), [validation](validation.json), [stream report](../../COLAB_RC5.md).
