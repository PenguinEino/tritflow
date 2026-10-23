# COLAB_RC stream brief: fresh-Colab Run all of the current pin

Write only under `docs/status/colab/v3-rc-2026-10-24/` and `docs/status/COLAB_RC.md`. Do not edit code,
notebooks or narratives. Do not commit.

Source: branch `notebook-v3` at commit `d9d2923` (notebooks pin `cc9a49e`), already pushed.
Repeat the procedure of `docs/status/colab/v3-release-2026-10-23/README.md` with the Colab CLI
(`~/.local/bin/colab new/exec/stop -s NAME`; see `docs/status/COLAB.md` for how earlier runs used it):
one fresh VM per language, open `notebook/v3/tritflow_en.ipynb` / `tritflow_ja.ipynb` from GitHub at
that commit, Run all, no overlay or upload. Stop each VM when done.

Record per language: rc, wall time including setup, KLayout and ngspice versions, the checks the
notebook prints (DRC/LVS/SPICE for the first circuit and dot4, the edited-HDL flow, the chapter 6
shuttle view: it must now show the stock OSS_FRAME with 16 pads), and every warning or error line.
Archive trimmed logs (step lines only, as in the 2026-10-23 folder; keep it under 50 KB) and a README
in the same style. If a run fails, retry once on a new VM; if it fails again, stop and report the cell,
the traceback and your diagnosis. If the Colab channel drops ("Connection was lost"), retry that run.
