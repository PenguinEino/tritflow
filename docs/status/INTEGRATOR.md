# Integrator queue and operating notes

## How the streams run
- Launch: `logs/run_stream.sh STREAM "extra"`; continue: `logs/resume_stream.sh STREAM SESSION_ID "prompt"`.
  Both use gpt-6.1-sol, reasoning effort xhigh, TR1UM_PDK=~/pdk/TR-1um-pinned. COLAB uses medium
  (resume manually with `-c model_reasoning_effort=medium`, DISPLAY=:1, cua_repl Chrome surface).
- Session IDs: CELLS 01a14de1-e546-73c3-b107-83224180c233, FRONTEND 01a14de1-e570-7390-8e6f-fbf5cf52108a,
  PNR 01a14de1-e575-7962-ac48-83f16782f534, SIM 01a14de1-e58e-79b0-8f5e-a66a20bfa06a,
  COLAB 01a14e20-608d-7be2-b35c-eb488ca8442b; STA, REVIEW, EDITOR: `grep "session id" logs/<S>.log`.
- Integrator commits and pushes to https://github.com/PenguinEino/tritflow (main) as
  52006822+PenguinEino@users.noreply.github.com; local pre-squash history in branch dev-history.

## Pending hand-offs (send when the stream's current run finishes)
- Pinned-PDK cascade: CELLS (phase 7, requalify) → PNR re-runs builds → SIM republishes →
  FRONTEND integrates. After CELLS publishes, tell PNR and SIM to re-run.
- FRONTEND phase 9 (after phase 8):
  (a) real-Colab fixes (docs/status/COLAB.md): Colab is Python 3.13 with pre-imported numpy; do not
      pin numpy/scipy/matplotlib/plotly (pin only klayout, lark) or force a runtime restart; print
      KLayout/ngspice versions; ch6/ch7 must not depend on ch0 globals. Setup took ~1 min on Colab.
  (b) copy root NOTICE into the submission folder and mention it in its licence section.
  (c) with EDITOR's notebook/narrative/: rebuild the notebook to docs/editorial.md — interactive layer
      (Plotly sliders/dropdowns over precomputed frames; ipywidgets only for live runs), predict-first
      hand estimates, teaser figure, Appendix A/B; move process/provenance text out of chapters.
- Integrator after cascade + FRONTEND phase 9: move tag colab-v0 to the new head, COLAB Run all on
  real Colab, then REVIEW round 2 focused on reader clarity and Code-a-Chip fit (not more caveats).
- Feature freeze 10-25 JST (docs/editorial.md schedule). STA, shuttle-ready top and corners enter
  the notebook only if clean by then.
