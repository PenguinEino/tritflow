# v3 RC3 check, fresh Colab VMs (CLI), 2026-10-29

Source: branch `notebook-v3`, notebook commit `96b3baa3042a4c1d54689408c91c2d9386de5324`, implementation pin `ff274b5db217aa10748977e5dfe59f6134f75a83`. Original notebooks fetched from immutable GitHub URLs and byte-compared with their git objects and `b8bf81a`. No overlay, upload or pin override. [URLs and hashes](source.json).

- English: **rc=0, 444.905 s including setup**, 31/31 cells, fresh-VM retry after a channel interruption.
- Japanese: **rc=0, 369.202 s including setup**, 31/31 cells, first attempt.

Both: **KLayout 0.30.6, ngspice-42, PDK 5d963db**. First circuit and dot4: **DRC 0 / LVS matched / SPICE pass**. Edited-HDL flow: **31 cells / 81 logically equivalent vectors / DRC 0 / LVS matched / SPICE PASS / maximum error 0.042 V**. Dot4 uses 11 transient intervals; edited HDL uses 11 sampled states, separately from exhaustive logical equivalence.

Chapter 6 scaling `c52`, power `c54` and timing `c56` completed with N=2/4/8/16; no stale-record or `NotReady` failure. Optional N=32 remains incomplete and excluded. Shuttle `c62` displays stock **OSS_FRAME with 16 actual pads**. Both viewer downloads match the signoff GDS hash and every stock-frame layer and transformed text. Both emit identical overview PNGs; that image was inspected. Japanese controls, result labels and pad directions are Japanese. Recorded shuttle DRC/LVS/precheck pass; organizer allocation, bond diagram and final CI remain. Scaling and shuttle signoff are recorded evidence, not newly rerun campaigns.

English attempt 1 lost its channel in `c41` (code cell 21/31), after 20 captured completed cells. Runtime API: idle kernel, zero connections. No notebook traceback or literal `Connection was lost`; local CLI interrupted with SIGINT, **rc=130, 286.180 s observed**, then VM stopped. This is not a completed-run time or a first-attempt pass. [Interruption](en-1-result.json), [kernel evidence](en-1-kernel-state.json).

No warnings, stderr outputs or errors in either successful notebook. CLI 0.7.4 repeatedly advertised 0.7.5. Separate audit-harness errors were recovered and preserved: source list/string comparison, missing local retry file before remote execution, and assuming Git metadata in the archived PDK. English frame audit used the saved viewer GDS and immutable GitHub PDK frame after shutdown; Japanese audit ran on its VM. [Harness notes](harness-notes.txt), [prelaunch traceback](en-2-prelaunch-error.txt), [probe traceback](en-2-probe-error.txt).

Timing surrounds `colab exec`, excluding allocation, audit and shutdown. Allocation plus successful execution: English **448.751 s**, Japanese **373.097 s**; English excludes its separately recorded prelaunch correction. CLI runs original code cells in order; browser interaction was not tested. All three owned VMs stopped; the unrelated pre-existing VM remained untouched. [Cleanup](cleanup.txt).

Evidence: [English steps](en-2-exec.txt), [Japanese steps](ja-1-exec.txt); [English result](en-2-result.json), [Japanese result](ja-1-result.json); [English output audit](en-2-audit.json), [Japanese output audit](ja-1-audit.json); [English chapter 6](en-2-chapter6.txt), [Japanese chapter 6](ja-1-chapter6.txt); [English shuttle](en-2-shuttle.json), [Japanese shuttle](ja-1-shuttle.json); [English notices](en-2-warnings.txt), [Japanese notices](ja-1-warnings.txt), [interrupted-run notices](en-1-warnings.txt), [interrupted steps](en-1-exec.txt).

Temporary originals, full outputs, images, helper scripts and local CLI state were removed after audit. The retained archive is below 50 KB. [Stream report](../../COLAB_RC3.md).
