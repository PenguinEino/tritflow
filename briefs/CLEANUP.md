# CLEANUP stream brief: leave only the v3 path in the repository

Work in `~/code-a-chip-cleanup` (branch `notebook-v3-cleanup`, from notebook-v3 f2dd9e3). Do not commit or
push; the integrator merges. Record every removal with its reason in `docs/status/CLEANUP.md`.

The submission is notebook v3 (`notebook/v3/tritflow_{ja,en}.ipynb`, built by `notebook/v3/make_notebook.py`).
Judges will browse this repository; AGENTS.md requires no dead code. V3 is editing in parallel:
`notebook/v3/narrative*/`, `notebook/views.py`, `notebook/scale_views.py`, `notebook/reuse.py`,
`notebook/v3/make_notebook.py` — do not edit those, except a minimal import-path change in the builder if a
move requires it (say so in the status file).

1. Build the dependency set of the v3 path: everything imported or read (directly or transitively, including
   files read by path, assets, recorded results and their reader checks) by the generated v3 notebook cells,
   the setup (`notebook/colab_setup.sh`, setup_colab, runtime locks), `notebook/reuse.py`, `notebook/scale_views.py`,
   `notebook/assets/chip/dot4/{build,verify}.py`, `examples/dot_scaling.py`, `submission/`, and the cell
   generation (`cells/`) and flow (`tritflow/`) code they use.
2. Remove what is outside that set: the v1 notebook and its builder/modules (`notebook/tritflow_tr1um.ipynb`,
   `make_notebook.py`, `methods.py`, `stages.py`, …), v2 (`notebook/v2/`: move `setup_cell.py` and
   `make_tables.py` — and anything else v3 imports from it — into `notebook/v3/`), recorded results/archives
   only v1/v2 used (e.g. `four_designs.zip`, old adder/load sweeps, paper evidence) and their stale-provenance
   tests, figure scripts only v1/v2 used, and obsolete briefs/status files only if nothing references them
   (keep docs/notebook-v2/STORYBOARD.md: its cross-cutting rules are still in force). Keep the tritflow library
   API and its own tests unless clearly unused by anything kept.
3. Rewrite the root `README.md` for the repository landing page in English: one paragraph on what TritFlow is,
   Open-in-Colab badges for `notebook/v3/tritflow_en.ipynb` and `tritflow_ja.ipynb` on branch `main`, the
   layout of the repository (what lives where), how to run locally, license. Short; no claims beyond the notebook.
4. Verify: `python3 notebook/v3/make_notebook.py` for both languages, execute both locally (ngspice-42 as in
   briefs/V3.md), all remaining test suites pass (`pytest` over tests/, notebook/tests if kept, submission/tests
   except the two expected stale-payload failures), and `git grep` finds no reference to removed paths.
