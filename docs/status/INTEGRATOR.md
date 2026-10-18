# Integrator queue and operating notes

## How the streams run
- Launch: `logs/run_stream.sh STREAM "extra"`; continue: `logs/resume_stream.sh STREAM SESSION_ID "prompt"`.
  Both use gpt-6.1-sol, reasoning effort xhigh, TR1UM_PDK=~/pdk/TR-1um-pinned. COLAB uses medium
  (resume manually with `-c model_reasoning_effort=medium`, DISPLAY=:1, cua_repl Chrome surface).
- Session IDs: CELLS 01a14de1-e546-73c3-b107-83224180c233, FRONTEND 01a14de1-e570-7390-8e6f-fbf5cf52108a,
  PNR 01a14de1-e575-7962-ac48-83f16782f534, SIM 01a14de1-e58e-79b0-8f5e-a66a20bfa06a,
  COLAB 01a14e20-608d-7be2-b35c-eb488ca8442b; EDITOR 01a14e83-d378-7cc0-8912-2a1a3d2b9558; STA, REVIEW: `grep "session id" logs/<S>.log`.
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
  (c) DEFERRED by the user until the pipeline is complete: rebuild the notebook to docs/editorial.md
      (interactive layer, predict-first estimates, Appendix A/B). Keep docs/editorial.md as the
      reference; paper-style static figures are made by the integrator in figures/.
- Integrator after cascade + FRONTEND phase 9: move tag colab-v0 to the new head, COLAB Run all on
  real Colab, then REVIEW round 2 focused on reader clarity and Code-a-Chip fit (not more caveats).
- Feature freeze 10-25 JST (docs/editorial.md schedule). STA, shuttle-ready top and corners enter
  the notebook only if clean by then.
- FRONTEND (next): add the `schematic()` delegate and a notebook cell after synthesis per SCHEM status (schematic stage built by SCHEM).
- DISPATCHED 10-18: SIM republish after synth change; FRONTEND phase 11 editorial integration (synth/hdl frozen). Next: regenerate figures, move colab-v0, COLAB round 3, REVIEW round 3.
- FRONTEND (after phase 12): REVIEW round-3 finding 5 table rows with run/seed identifiers (paper adder seed 7 vs archive seed 0); integrate EDITOR phase-3 text (sizing sign explanation); finding 6: attendance confirmed by the user (docs/author.md) — replace the placeholder and regenerate the package.

## State 2026-10-19 (after plan review)
- Release candidate history: colab-v0 = 6d8df9e (real Colab round 4 on 2c81d2c passed, 18 cells, 405 s, one Run-all retry; round 5 on 6d8df9e running).
- Plan review (docs/editorial.md, last section): code-as-method refactor (FRONTEND phase 15) and reuse story (EDITOR phase 4: ch7 STA, ch9 shuttle-ready top, Appendix C, README final).
- Integrator to do: write README.md from notebook/narrative/readme_final.md; regenerate figures only in the release step (python3 figures/make_all.py) BEFORE FRONTEND captures hashes; then retag colab-v0, COLAB round 6, REVIEW round 4 (reader + Code-a-Chip fit), user read-through, freeze 10-25, user opens PR 10-30.
- Other streams idle: CELLS, PNR, SIM, STA, SCHEM (done). Live log viewers: tail -F logs/<S>.log.
- DONE by integrator 08722c4: Appendix A prose tables -> wrapped paragraphs (notebook/markdown_support.py), larger fig_flow text, darker sizing series. FRONTEND phase 15 rebuild must keep markdown_support._prose_list and embed the regenerated figures.

## State 2026-10-19 (integrator took over the notebook directly)
- 91f642d (tag colab-v0): code-as-method refactor done by the integrator. Visible method cells live in
  notebook/methods.py; collapsed checks in notebook/stages.py; builder notebook/make_notebook.py adds
  '#@title' form cells. Chapter 8 = method-custom → custom_check → method-custom_layout → custom.
  New: ch7 STA live cell, ch9 shuttle snapshot (notebook/assets/chip/adder4), Appendix C, README.
- Release procedure (any notebook/*.py or ipynb change invalidates the recorded four-design campaign):
  make_notebook.py → validate_notebook.py --execute (fresh, ~7 min) → PYTHONPATH=.:notebook
  python3 notebook/campaign.py build/notebook/cache → submission/build_submission.py → commit → tag colab-v0.
  Figures: regenerate (figures/make_all.py) and then notebook/paper_evidence.py --refresh-presentation BEFORE make_notebook.
- FRONTEND stream was interrupted at the user's request; it may be resumed for later work, but notebook/
  is now edited by the integrator.
- Pending release: fig_gates recoloured (refresh paper evidence + full release procedure together with SCHEM phase 5).
- 10-19: colab-v0 = 020fc73 (Colab round 10 on 0ffe7a1 passed first Run all, 35 cells, 300.7 s). ch4 fig_synth redrawn (FIGSYNTH), ch5 trit selector over flat schematic (notebook/learning.py value_selector; submission packs its default view), SCHEM phase 6 Colab sizing. Japanese one-off review copy at build/review_ja/ (untracked; user reviewing). Next: user feedback from JA review, REVIEW round 4, freeze 10-25.
