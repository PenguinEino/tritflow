# v3 RC check, fresh Colab VMs (CLI), 2026-10-24 — stopped

Source: branch `notebook-v3`, notebook commit `d9d292395cd4e801b6055ff4606f82ed5499f6d1`, implementation pin `cc9a49e97e1ad098743494db7d82adb34a379bbe`. The original English notebook was downloaded from GitHub at that immutable commit and byte-compared with `git show`. No overlay, upload, source override, or notebook edit. Colab CLI 0.7.4, fresh standard CPU VMs.

**Qualification failed and was stopped at the integrator's request. Japanese was not started.** A new pin will be tested only on a new request.

## Attempts and progress

| Attempt | Outcome |
|---|---|
| English 1, `tritflow-rc-20261024-en-1` | Local controller lost during the model/session transition, while setup was running. Its CLI child and VM were stopped; the first stop explicitly confirmed `Session terminated`. No notebook exception. Complete rc/wall time unavailable. |
| English 2, `tritflow-rc-20261024-en-2` | Setup and first circuit passed. VM disappeared at code cell 9/31 (`c18`, zero-based notebook index 18, cell truth tables). Status pruned the stale session; backend inventory confirmed absence. No Python traceback or literal `Connection was lost` line. Waiting local CLI was then terminated with SIGTERM: rc=-15, observed execution wall time 301.128 s including setup; allocation 4.031 s. This is an interrupted duration, not a completed-run time. Cause unknown. |
| English 3, `tritflow-rc-20261024-en-3` | First circuit and dot4 passed. Scaling failed at code cell 26/31 (`c52`, notebook index 52); dependent cells 27/31 and 28/31 raised `NotReady`. CLI continued through all 31 cells. The integrator then cancelled qualification; complete rc/wall time were not recorded. |
| Japanese | Not started. |

English 3 printed **KLayout 0.30.6, ngspice-42, PDK 5d963db**. Before scaling: first circuit and dot4 each had **DRC 0 / LVS matched / post-layout SPICE within the ±0.5 V band in every interval**. No other notebook warning or exception was captured before scaling. Dot4 used 46 cells and passed logical equivalence for 6561 input vectors.

The captured failure agrees with the integrator's diagnosis of stale recorded scaling after the `chip_power.py` change:

```text
RuntimeError: Recorded dot scaling is stale: source/tritflow/pnr/chip_power.py, source/tritflow/pnr/chip_power.py
```

Full available traceback and both dependency errors: [en-errors.txt](en-errors.txt). **CLI 0.7.4 continues after notebook cell exceptions**, so reaching later cells does not establish a successful Run all. Progress-only lines must be audited alongside error outputs. Before cancellation, its continued edited-HDL flow printed 31 cells, equivalence for 81 vectors, DRC 0, LVS matched, and post-layout SPICE PASS with maximum error 0.042 V. Shuttle cell `c62` emitted four display outputs; independent stock-frame/pad verification was cancelled and is not claimed.

## Evidence and cleanup

- [English final-attempt step log](en-exec.txt), [result](en-result.txt), [tracebacks](en-errors.txt), [warning/notice lines](warnings.txt).
- [Interrupted attempt 1 steps](en-interrupted-1-exec.txt), [attempt 2 steps](en-interrupted-2-exec.txt), [attempt 2 timing](en-interrupted-2-result.json).
- Explicit `colab stop -s NAME` was issued for **all three owned names** after the stop instruction; all returned session not found. [Stop results](stop-results.json).
- [Final backend inventory](cleanup.txt) contains only the same two pre-existing unrelated CPU sessions. No owned VM or local runner remains. No Japanese VM was created.

Untrimmed logs, downloaded notebook copies, output notebook, and temporary controllers were removed after preserving the evidence. The archive is under 50 KB. No implementation, notebook, narrative, git state, or unrelated session was changed by this stream; no local packages were installed.
