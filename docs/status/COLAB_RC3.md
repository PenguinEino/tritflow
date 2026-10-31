# COLAB_RC3 — complete, 2026-10-29

Both editions completed all 31 code cells on fresh standard CPU Colab VMs. English passed after a channel-drop retry; Japanese passed on its first attempt. All three owned VMs are stopped.

| Edition | CLI rc | Wall time including setup | Allocation + execution |
|---|---:|---:|---:|
| English, successful retry | 0 | 444.905 s | 448.751 s |
| Japanese, first attempt | 0 | 369.202 s | 373.097 s |

Notebook commit `96b3baa3042a4c1d54689408c91c2d9386de5324`, implementation pin `ff274b5db217aa10748977e5dfe59f6134f75a83`. Both original notebooks were fetched from GitHub and byte-compared with their git objects and `b8bf81a`. No overlay, upload, pin override or notebook edits. Tools: KLayout 0.30.6, ngspice-42, PDK 5d963db.

Both editions passed the required checks:

- First circuit and dot4: DRC 0, LVS matched, extracted SPICE within ±0.5 V in every tested interval.
- Edited HDL: 31 cells, 81 logically equivalent vectors, DRC 0, LVS matched, SPICE PASS, maximum error 0.042 V.
- Scaling `c52` and dependent `c54`/`c56`: N=2/4/8/16 tables completed without stale-record or `NotReady` errors.
- Shuttle `c62`: viewer GDS matches signoff; stock OSS_FRAME geometry and transformed text match exactly; 16 actual pads. Japanese controls, check labels and pad directions verified in saved output. Both editions emitted the same overview image, which was inspected.

Dot4 transient coverage is 11 intervals; edited HDL uses 11 sampled states, separately from exhaustive logical equivalence. Scaling and shuttle signoff are recorded evidence. Optional N=32 remains incomplete; shuttle submission preparation still requires organizer allocation, final bond diagram and final CI.

English attempt 1 lost output during `c41`, after 20 captured completed cells. Runtime API showed an idle kernel with zero connections. No notebook traceback or literal “Connection was lost” appeared. The waiting CLI was interrupted with SIGINT (rc 130; 286.180 s observed), its VM stopped, and the notebook retried on a fresh VM as instructed. First-attempt reliability is therefore not a pass.

No notebook warnings, stderr outputs or exceptions in either completed run. Exact CLI update notices are archived. Three harness issues are separately documented: source list/string normalization, a missing local notebook before the retry's first remote execution, and a post-run probe expecting Git metadata in the archived PDK. English frame verification recovered offline using the actual saved viewer GDS and immutable GitHub PDK frame. Japanese remote verification passed and confirmed the expected implementation HEAD with no tracked changes. These were harness issues, not notebook failures; available tracebacks are retained.

Decisions: use original defaults, supplied edited HDL and recorded scaling; inspect outputs as well as rc; measure setup-inclusive execution separately from allocation/audit/shutdown; isolate CLI session/history/settings records; leave the unrelated existing CPU VM untouched. Browser interaction was outside this CLI brief. No extra local packages installed.

[Archive README](colab/v3-rc3-2026-10-29/README.md) links step logs, timing, diagnostic audits, chapter 6 output, frame checks, harness tracebacks and cleanup. The archive is below 50 KB; temporary notebooks, large outputs, helpers and CLI state were removed. Reproduction: fetch immutable URLs in `source.json`; run `colab new -s NAME`, `colab exec -s NAME -f ORIGINAL.ipynb --timeout 1200`, audit outputs, then `colab stop -s NAME` per language. No owned pytest suite applies to these evidence-only paths; real Colab execution and artifact/cleanup checks provide verification.

Done: all brief requirements. In progress: none. Blockers: none. Interface requests: none. Only authorized status paths changed; no implementation/narrative edits, commits or pushes.
