# v3 RC2 check, fresh Colab VMs (CLI), 2026-10-24

Source: branch `notebook-v3`, notebook commit `e20285092edae03af7a263e99f60fb907dcdaddc` (implementation pin `163b13725249e49874ac6ae6bc61bd49e9483832`). Both original notebooks were fetched from immutable GitHub URLs and byte-compared with their git objects. No overlay, upload or pin override; each notebook fetched its pinned implementation from GitHub. [Source URLs and hashes](source.json).

- English: **rc=0, 397.148 s including setup**, 31/31 code cells, first attempt.
- Japanese: **rc=0, 423.200 s including setup**, 31/31 code cells, first attempt.

Both: **KLayout 0.30.6, ngspice-42, PDK 5d963db**. First circuit and dot4: **DRC 0 / LVS matched / post-layout SPICE pass**. Edited-HDL full flow: **31 cells / 81 equivalent input vectors / DRC 0 / LVS matched / SPICE PASS / maximum error 0.042 V**. The dot4 transient uses the notebook's 11 intervals; the edited-HDL transient uses its default 11 sampled states, separately from the exhaustive logical equivalence check.

Chapter 6 scaling `c52` and dependent `c54`/`c56` all completed. N=2/4/8/16 tables were displayed without stale-record or `NotReady` errors. The recorded optional N=32 P&R attempt is explicitly incomplete and excluded.

Shuttle `c62`: the displayed/downloadable GDS matches its signoff hash, contains stock **OSS_FRAME with 16 pads P01–P16**, and matches every stock-frame layer and transformed text. Both editions emitted the same overview PNG; its image was inspected. Japanese viewer controls, check/result labels, pad directions and remaining-submission note are Japanese. Recorded drawing/mask DRC=0, drawing LVS matched and MPW precheck PASS; submission preparation remains unfinished pending organizer allocation, the final bond diagram and final CI. Shuttle signoff/scaling are recorded evidence, not campaigns rerun by this notebook.

No notebook warnings, stderr outputs, exceptions or channel drops. The only CLI notice was the available 0.7.5 update from installed 0.7.4; every repeated notice is retained in the warning/cleanup files. No retry was needed. Both owned VMs were stopped and verified absent; the same two unrelated pre-existing CPU VMs were left untouched.

Timing surrounds `colab exec`, including setup, and excludes VM allocation, the subsequent read-only frame audit and shutdown. Including VM allocation: English 400.884 s, Japanese 427.982 s. The CLI executes the original code cells in order; qualification checks all saved outputs as well as rc. Interactive browser behavior was not tested in this CLI run.

Evidence: [English steps](en-1-exec.txt), [Japanese steps](ja-1-exec.txt); [English result](en-1-result.json), [Japanese result](ja-1-result.json); [English output audit](en-1-audit.json), [Japanese output audit](ja-1-audit.json); [English chapter 6](en-1-chapter6.txt), [Japanese chapter 6](ja-1-chapter6.txt); [English shuttle audit](en-1-shuttle.json), [Japanese shuttle audit](ja-1-shuttle.json); [English warnings](en-1-warnings.txt), [Japanese warnings](ja-1-warnings.txt); [cleanup](cleanup.txt).

Temporary notebooks, complete output/image payloads, controller scripts and isolated CLI session state were removed after audit. The retained archive is below 50 KB. [Stream report](../../COLAB_RC2.md).
