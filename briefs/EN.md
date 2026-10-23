# EN stream brief: English edition of notebook v3

Work in `~/code-a-chip-v3-en` (branch `notebook-v3-en`, forked from `notebook-v3`). Do not commit or
push; the integrator merges your branch into `notebook-v3`. Another stream (V3) is still changing
`notebook-v3` in parallel (chapter 6, a fix in 5-3), so keep your edits small and mechanical in shared
files to make the merge easy. Record decisions in `docs/status/EN.md`.

The English notebook is the primary submission for the international Code-a-Chip ISSCC 2027 jury;
the Japanese one is a companion. Same cell structure, same figures, same interactions.

1. Language switch for everything the notebook prints: step logs and error boxes (`notebook/live.py`),
   tables, notes, conditions and widget labels (`notebook/views.py`, `cell_views.py`, `pnr_views.py`,
   `inverter_views.py`, `tritflow/viz`), schematic labels (`tritflow.schematic.set_language` already
   exists — follow that pattern: one module-level language, Japanese default so v2/v3-ja stay byte-
   identical in output). The table pictures under `notebook/assets/tables/` need English variants
   (`notebook/v2/make_tables.py`). Figures in `figures/out/*_ja.png` have English counterparts already
   (`*.png` without `_ja`); check.
2. Builder: `notebook/v3/make_notebook.py --lang en` produces `notebook/v3/tritflow_en.ipynb` from
   `notebook/v3/narrative_en/*.md` and English code cells (the code is identical; only the cell title
   comments and the strings passed to step()/need()/note() are translated — keep one CODE definition
   with the language-dependent strings looked up, not two copies of every cell).
3. Translate chapters 0–5 (`notebook/v3/narrative/00–05`) into `narrative_en/`. Register: concise
   technical English for IC designers (an ISSCC paper's tone), standard terms (place and route, logic
   synthesis, extraction, post-layout simulation, DRC/LVS), no marketing words, no paraphrase of what
   outputs show. Keep every number and claim exactly; keep math as is.
4. Verify: build both languages, execute both locally (see `briefs/V3.md` for the command), no errors;
   the Japanese output must be unchanged apart from what V3 changes. Render a few English outputs to PNG
   with headless Chrome and look at them.
Chapter 6 is translated later, when V3 has finished it.

## Round 2 (2026-10-23 evening): sync with notebook-v3 and finish the English edition

1. In `~/code-a-chip-v3-en`, merge `origin/notebook-v3` (head bfebe83) into `notebook-v3-en`; resolve
   conflicts keeping both V3's content (chapter 6, 5-3 step, reuse/scale views) and your language switch.
   Commit the merge locally is NOT allowed — leave it staged/uncommitted; the integrator commits.
   (If git requires a commit to finish the merge, stop at the resolved, staged state.)
2. Translate what changed in Japanese since your round 1: opening (author block, paragraphs 1–3, chapter
   reference), §2.1 worked numbers and RR definition, §3.1 X/Z sentence, §3.3 fanout reason, §3.7 BitNet
   sentence and forward reference, §5.3 coverage sentence, chapter-5 ending; and all of chapter 6 into
   `narrative_en/06_results.md`, including the reference list (keep citations exact). English strings
   for every new chapter-6 cell and view (`notebook/scale_views.py`, `notebook/reuse.py`, chapter-6 cells).
3. Apply the English edits from `docs/status/REVIEW_V3.md` §7, and add to the English opening an
   "Open in Colab" badge link for `notebook/v3/tritflow_en.ipynb` on the published branch plus one line:
   Run all takes about 7 minutes on a fresh Colab runtime (setup about 2 minutes).
4. Visual fixes (both languages): in the chapter-6 power figure the legend collides with the Plotly
   mode bar — move the legend or hide the mode bar; the three note lines under 6-1 must use the same
   note style/font as the other notes.
5. Build and execute both languages locally (ngspice-42 as in briefs/V3.md), no errors; Japanese outputs
   unchanged except the visual fixes; render chapter 6 in English to PNG and look at it. Record in
   docs/status/EN.md.
