# COLAB_RC5 stream brief: fresh-Colab Run all of the release candidate

Write only under `docs/status/colab/v3-rc5-2026-10-31/` and `docs/status/COLAB_RC5.md`. Do not edit code,
notebooks or narratives. Do not commit.

Source: branch `notebook-v3` at commit `fcdde92` (notebooks identical to `d7e5d0e`, implementation pin `7a33860`), already pushed.
Repeat the procedure of `docs/status/colab/v3-release-2026-10-23/README.md` with the Colab CLI
(`~/.local/bin/colab new/exec/stop -s NAME`; see `docs/status/COLAB.md` for how earlier runs used it):
one fresh VM per language, open `notebook/v3/tritflow_en.ipynb` / `tritflow_ja.ipynb` from GitHub at
that commit, Run all, no overlay or upload. Stop each VM when done.

Record per language: rc, wall time including setup, KLayout and ngspice versions, the checks the
notebook prints (DRC/LVS/SPICE for the first circuit and dot4, the edited-HDL flow, the chapter 6
shuttle view: it must show the stock OSS_FRAME with 16 pads and Japanese labels in the ja edition; the chapter 6 scaling cell must run), and every warning or error line.
Archive trimmed logs (step lines only, as in the 2026-10-23 folder; keep it under 50 KB) and a README
in the same style. If a run fails, retry once on a new VM; if it fails again, stop and report the cell,
the traceback and your diagnosis. If the Colab channel drops ("Connection was lost"), retry that run.

## New in this round (check explicitly)
- Section 6.5 (cell `6-6`) now builds the MPW full chip live: it clones the organizer template
  `munetomo-maruyama/TR-1um_MPW_Sanken` at a pinned commit and runs full signoff (about 90 s locally).
  Record its wall time on Colab, its step line (pads, all checks pass) and that the pad table shows 16 pads.
- Chapter 7 Playground (cell `7-1`) runs the full flow on `add2` and shows schematic, P&R replay, GDS,
  wire-capacitance table, waveforms and summary. Confirm every view appears and the run passes.
- Record total wall time per language; the notebook states "6〜8分" and this may need updating.
- Deadline context: finish and report by 2026-10-31 22:45 JST at the latest.

## RC5 specifics
- RC4 failed because the organizer precheck child process could not import `pya`
  (docs/status/COLAB_RC4.md). Cell 6-6 now prepends the kernel's KLayout module directory to
  `PYTHONPATH` before `to_chip`. Confirm the precheck passes and the chip view (GDS, checks, 16-pad
  table) appears.
- **Run English and Japanese in parallel on two fresh VMs** to save time. Same retry rules.
- Report the total wall time per language and the 6-6 cell time separately.
