# Brief: COLAB stream — verify the notebook on real Google Colab

You own `docs/status/COLAB.md` and `logs/colab/` only. Do not edit any other file and do not run
git write commands.

## Task
Use your computer-use / browser tools on this machine's desktop to:
1. Open https://colab.research.google.com/github/PenguinEino/tritflow/blob/colab-v0/notebook/tritflow_tr1um.ipynb
2. Connect a standard (free, CPU) runtime and run all cells (Runtime → Run all). Colab's warning that
   the notebook comes from GitHub ("Run anyway") may be accepted — the notebook is the user's own.
3. Wait for completion (the setup cell installs ngspice, KLayout and the PDK; allow ~15 min).
4. For every cell record: ran / error, wall time if shown, and the first lines of any traceback.
   Save screenshots of the setup output, of each chapter's main figure, and of every error to
   `logs/colab/` (PNG, numbered in notebook order).
5. Report in `docs/status/COLAB.md`: overall result, runtime of the setup cell and of Run all, the
   printed tritflow commit hash, KLayout / ngspice versions printed, every failing cell with its
   traceback text, and anything that looked wrong in figures (blank, clipped, unreadable in the
   Colab theme).

## Limits
- Never type passwords or other credentials, never sign in or create accounts, never change Google
  account settings, never grant OAuth permissions. If Colab requires sign-in, stop and report that
  the user must sign in in this machine's browser.
- Do not save the notebook to Drive or GitHub, do not share it, do not upgrade to paid tiers.
- Disconnect and delete the runtime when finished (Runtime → Disconnect and delete runtime).
