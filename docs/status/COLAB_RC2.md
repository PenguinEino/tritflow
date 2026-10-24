# COLAB_RC2 — complete, 2026-10-24

**Both languages passed on their first fresh standard CPU Colab VM. All 31 code cells completed in each language, with no notebook warnings, stderr outputs or exceptions. Both VMs are stopped.**

| Edition | CLI rc | Wall time including setup | Including VM allocation | Attempts |
|---|---:|---:|---:|---:|
| English | 0 | 397.148 s | 400.884 s | 1 |
| Japanese | 0 | 423.200 s | 427.982 s | 1 |

Source notebook commit: `e20285092edae03af7a263e99f60fb907dcdaddc` on `notebook-v3`; implementation pin: `163b13725249e49874ac6ae6bc61bd49e9483832`. Both notebooks were downloaded from immutable GitHub URLs and byte-compared with the corresponding local git objects. Original cells ran in order through Colab CLI 0.7.4, without overlay, upload, pin override or notebook/source changes. Post-run probes confirmed the expected implementation HEAD and no tracked source changes.

## Required checks

Both editions printed **KLayout 0.30.6, ngspice-42 and PDK 5d963db**.

| Check | English | Japanese |
|---|---|---|
| First circuit | DRC 0; LVS matched; SPICE within ±0.5 V in every interval | Same |
| Dot4 | DRC 0; LVS matched; SPICE within ±0.5 V in every interval | Same |
| Edited-HDL example, c60 | 31 cells; 81 logically equivalent input vectors; DRC 0; LVS matched; SPICE PASS; max error 0.042 V | Same |
| Chapter 6 scaling, c52 | N=2/4/8/16 tables displayed; no stale-record failure | Same |
| Dependent scaling cells, c54/c56 | Power and timing outputs completed; no `NotReady` | Same |
| Chapter 6 shuttle, c62 | Stock OSS_FRAME; 16 pads; four display outputs | Same; Japanese labels verified |

The dot4 transient checks the original 11 intervals with fixed weights; its logical equivalence check covers all 6,561 input vectors. The shipped edited-HDL example uses 11 sampled transient states, separately from its 81-vector exhaustive logical equivalence check. No claim of exhaustive transient coverage is made.

The shuttle viewer's downloadable GDS SHA-256 is `6d2453708f58a442dbf151d4afe6bb77d4c9f3e1b813807a781c6068a592f6dd`, matching the signoff record and audited file. A read-only probe on each VM compared every stock-frame layer and transformed text against the pinned PDK: zero geometry differences and zero text differences. Both display pad rows P01–P16 and emit the same overview PNG; that actual image was inspected. Japanese output includes `全体表示`, `座標の単位：µm`, `検査（記録済み）`, `提出準備 / 未完了`, `信号 / 電源`, `方向`, `電源 / 入力 / 出力`, and the Japanese remaining-submission note.

Recorded shuttle checks display drawing DRC 0, drawing LVS matched, mask DRC 0 and MPW precheck PASS. `submission_ready=false` remains explicit: organizer allocation of the full slot, final bond diagram and final CI remain. The recorded optional N=32 scaling attempt is incomplete at P&R and excluded. These are displayed scope limitations, not new notebook failures. Scaling and shuttle signoff were loaded/verified as recorded evidence; their campaigns were not recomputed.

## Warnings, decisions and cleanup

- No notebook warning, error output, stderr output, traceback or channel drop in either run; no retry needed. The prior RC's `c52` stale-scaling failure did not recur.
- CLI 0.7.4 printed its three-line 0.7.5 update notice during new/exec/probe/stop and final checks. Exact notices are retained per language and in the cleanup log. No CLI upgrade or extra local Python package installation.
- Wall time is measured around `colab exec`, including setup. Allocation is separately reported; frame audit and shutdown are excluded. CLI rc alone was insufficient: all saved cell outputs were audited.
- Used the original defaults, including the supplied edited-HDL example and recorded scaling. Additional remote code only read the completed runtime identity and shuttle artifacts; it did not change notebook cells or rerun a flow.
- English `tritflow-rc2-20261024-en-1` and Japanese `tritflow-rc2-20261024-ja-1` both returned `Session terminated`; final status reports both not found. Backend inventory contains only the same two pre-existing unrelated CPU sessions. They were not stopped.
- Work stayed within the two authorized status paths. Temporary originals, full output notebooks/logs/images, helper scripts and isolated session state were removed after extracting compact evidence. No code/narrative edits, git-state changes, commits or pushes.

## Evidence and verification

[Archive README](colab/v3-rc2-2026-10-24/README.md) links the per-language step logs, timing, full-cell error audits, chapter 6 output excerpts, frame/display checks, exact CLI notices and cleanup results. The archive contains 15 files totaling 32,879 bytes, below 50 KB.

Procedure: download the original notebook URL in `source.json`, then `colab new -s NAME`, `colab exec -s NAME -f ORIGINAL.ipynb --timeout 1200`, and `colab stop -s NAME`; this run used an isolated `--config` file. Validate all saved notebook outputs, not only rc. No owned pytest suite applies to these evidence-only paths. Actual Colab execution and artifact/cleanup checks are complete. Browser interaction/zoom behavior was outside this CLI brief.

Done: all brief requirements. In progress: none. Blockers: none. Interface requests: none.
