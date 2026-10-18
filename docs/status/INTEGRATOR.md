# Integrator queue

Pending hand-offs (send when the stream's current run finishes):

- CELLS (after timing tables): requalify all cells against the pinned PDK
  (~/pdk/TR-1um-pinned, commit 5d963db): DRC, LVS, abutment, equivalence; republish atomically.
- Integrator after all republish: move tag colab-v0 to the new head (REVIEW finding 1),
  re-run REVIEW on the new head.
- FRONTEND (after phase 8): copy root NOTICE into the submission folder and mention it in its README licence section.
- FRONTEND (after phase 8): real-Colab findings in docs/status/COLAB.md — Colab is Python 3.13 with
  preinstalled/pre-imported numpy; pinning numpy/scipy/matplotlib in requirements-colab.txt mixes
  versions in the live kernel (`numpy._core._multiarray_umath` lacks `_blas_supports_fpe`). Use
  Colab's own numpy/scipy/matplotlib/plotly (pin only klayout, lark), or force a runtime restart
  after install; print KLayout/ngspice versions in setup; make chapter 6/7 not depend on chapter-0
  globals (or fail with a clear message). Setup took ~1 min on Colab.
- COLAB: rerun on the new colab-v0 after the fixes.
