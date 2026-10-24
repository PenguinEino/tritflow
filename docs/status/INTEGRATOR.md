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
- 10-19 release order (immutable source pin): (1) release steps + commit implementation X; (2) make_notebook
  now pins X (SOURCE_REF = full SHA of HEAD); validate + build_submission + tests; commit Y (notebook only);
  (3) tag colab-v0 -> Y, push. The campaign manifest hashes the notebook without its SOURCE_REF line
  (notebook/cache.py notebook_hash), so step 2 does not invalidate recorded experiments.

## State 2026-10-23 (notebook v3)
- Review against Code-a-Chip criteria → v3 on branch `notebook-v3`, worktree `~/code-a-chip-v3`
  (decisions: `docs/notebook-v3/STORYBOARD.md`). dot4 carries ch. 3–5; ch. 6 gathers results.
- Work is done by the V3 codex stream (gpt-6.1-sol, reasoning effort max, brief `briefs/V3.md`,
  session 01a167ae-d5f7-75f2-b52c-f179b59c74a4, log `~/code-a-chip-v3/logs/V3.log`). Launch/resume from
  `~/code-a-chip-v3` with `codex exec [resume ID] -C ~/code-a-chip-v3 -m gpt-6.1-sol -c model_reasoning_effort=max`.
  The integrator reviews, polishes Japanese text with yomiyasu and commits.
- Open: first fresh-Colab run stalled in 5-3 (ngspice-42 vs local 46); second run pending.
- 10-23 parallel streams (all gpt-6.1-sol, effort max; launcher `logs/launch.sh STREAM WORKDIR [--search]`):
  EN 01a167b0-ea8f-7b10-89ed-4bb6768b308b (worktree `~/code-a-chip-v3-en`, branch `notebook-v3-en`, merge into notebook-v3),
  REFS 01a167b0-eaed-76d0-adda-75b348a57352 (`docs/references.md`, web search),
  SUBMIT 01a167b0-eb26-78a0-a6ee-b3ae10edb1ea (`submission/` for v3, EN primary + JA companion).
- 10-23 chapter 6 split: SCALE 01a167b3-f64c-7c03-91d2-8f8461d4bb5c (scaling data, `notebook/scale_views.py`),
  SHUTTLE 01a167b3-f6b2-7460-bcb5-6588a7575056 (`notebook/reuse.py`, dot4 MPW top); V3 resumed with phase 2
  narrowed to integrating chapter 6 (narrative + builder cells).
- 10-23 night: main stays at v1 until the author approves updating it. Colab badges (README, English opening)
  point to branch notebook-v3 meanwhile; switch them to main when main is updated.

## State 2026-10-23 late (v3 release candidate)
- Branch notebook-v3 (worktree ~/code-a-chip-v3) is the submission source; main still v1 (author: wait).
  Chapters 0-6 in Japanese and English; v1/v2 removed (CLEANUP). Reviews are done by Claude itself.
- Release candidate: notebooks pinned to 8f77584; fresh-Colab Run all passed (en 372 s, ja 447 s,
  docs/status/colab/v3-release-2026-10-23); payload c62518d, `build_submission.py --check --require-final`
  passes (submission_ready true), 9.9 MB.
- Release procedure: (1) commit implementation W; (2) make_notebook --lang ja/en pins W, commit X;
  (3) at HEAD, `TRITFLOW_REF=$(git rev-parse HEAD) python3 submission/build_submission.py` (the gate needs
  the execution commit to equal the evidence source_ref; the pinned W must hold the same notebook up to
  its own stamp); (4) `--check --require-final`; commit the payload.
- Open: author approval to update main (then switch Colab badges in README and the English opening to
  main and redo steps 1-4); the PR to sscs-ose is the author's action on 10-30.

## State 2026-10-24 (release candidate 2)
- Since RC1: stock OSS_FRAME dot4 top (FRAME, FIXSCALE), sliders, ch. 2.1 list, ch. 4 retry counts,
  opening lead + early flow figure, shorter submission README (README_TRIM), visual fixes (VISFIX),
  Wang 2021 spelling. Reports: ACCEPTED, LINKS, NUMBERS, VISUAL, VISFIX, FIXSCALE, README_TRIM.
- Codex streams: gpt-6-astra xhigh, service tier priority (logs/launch.sh, logs/resume.sh).
- Release procedure, corrected (the one-step pin failed twice): (1) commit all source and narrative
  changes, W; (2) make_notebook --lang ja/en --ref W, commit X — X now holds the current notebooks;
  (3) make_notebook --ref X, commit Y — identical to X's notebooks up to the stamp; (4) at Y,
  `TRITFLOW_REF=$(git rev-parse HEAD) python3 submission/build_submission.py`, then
  `--check --require-final`, commit the payload. Recorded campaigns hash source files
  (results/dot_scaling.json, dot4 provenance): never edit a hashed file without checking.
- Delivery month: January 2027 stays. The organizer told the author delivery within January 2027 is
  likely (provisional), so the text is unchanged.
- COLAB_RC2 (fresh Colab, notebooks e202850, pin 163b137): ja and en passed on the first VM, 31 code
  cells each, no warnings; ch. 6 scaling and the 16-pad stock frame displayed (docs/status/COLAB_RC2.md).
