# Brief: EDITOR stream — the notebook's story

You own `notebook/narrative/` and `docs/status/EDITOR.md`. You do not edit code or the .ipynb;
FRONTEND integrates your text. No git write commands.

Read first: `docs/editorial.md` (binding), `docs/concept.md`, the current notebook
(`notebook/tritflow_tr1um.ipynb`, read its markdown and outputs), and the status files of all
streams for the real numbers. Past winning notebooks for tone:
https://github.com/sscs-ose/sscs-ose-code-a-chip.github.io (ISSCC25/26, VLSI26 accepted folders).

## Deliverables
1. `notebook/narrative/00_intro.md` … `09_next.md`, `A_limits.md`, `B_evidence.md`: the reader-facing
   text for every chapter in `docs/editorial.md`'s storyboard and template. Numbers are never typed:
   write placeholders like `{adder.die_um}` and list each placeholder with its exact data source
   (file + JSON path or API call) in `notebook/narrative/placeholders.md`.
2. For each "Predict first" step, the hand-estimate math (LaTeX) plus the variables it needs and where
   they come from (PDK model parameters, cell sizes, char.json), so FRONTEND can compute it.
3. `notebook/narrative/figures.md`: for each chapter, the hero figure spec (what is plotted, axes,
   annotations, interaction) — concrete enough to implement.
4. A teaser for the top of the notebook: one figure spec + two sentences.
5. `notebook/narrative/pitch.md`: title options, a 3-sentence pitch, a 100-word abstract, and a
   one-paragraph "why ternary, why this PDK, why now" for the README and PR description.

## Style
Follow `docs/editorial.md` strictly: story and figures in chapters, limits once in Appendix A,
evidence and run notes in Appendix B, ≤ 25 minutes of reading, plain expert English, no internal
process words, no TODOs. Be honest: the cells were taped out but silicon is not yet measured.
