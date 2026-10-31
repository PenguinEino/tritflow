# REVIEW_JA6 stream brief: jury review of notebook v3 with chapter 6

Work in `~/code-a-chip-v3`. Write only `docs/status/REVIEW_JA6.md`. Report only: do not edit code,
narrative, assets or results; do not commit.

Act as a member of the IEEE SSCS Code-a-Chip ISSCC 2027 jury. Calibrate with the official rules
(github.com/sscs-ose/sscs-ose-code-a-chip.github.io README/FAQ/howtoapply) and the accepted notebooks
already discussed in `docs/status/REVIEW_V3.md` (the previous review of chapters 0–5; read it first and
do not repeat what it already says unless it is still unresolved).

Review the Japanese notebook `notebook/v3/tritflow_ja.ipynb` as executed
(`build/v3/tritflow_ja_out.ipynb`; render chapter 6 outputs with headless Chrome and look at them), the
narrative `notebook/v3/narrative/*.md`, the recorded data `results/dot_scaling.json`
(+ `docs/status/SCALE.md`), `notebook/reuse.py`, `notebook/assets/chip/dot4/` and
`submission/templates/{PITCH,ABSTRACT,README}.md`. The English edition is being produced in parallel;
judge substance, not English wording.

Report, ranked by impact on acceptance, concrete (quote text / name the cell, why, proposed change):
1. Verdict now: select / shortlist / reject, and the single biggest remaining reason.
2. Does chapter 6 deliver what the opening and chapters 0–5 promise? Missing or weak evidence, numbers
   an expert would distrust (methodology of power, STA comparison, area, N=16 non-default routing,
   N=32 failure), and whether the conclusion says what the data show.
3. Claims that are still overstated or unsupported anywhere (opening, conclusion, pitch, abstract).
4. Structure and reading load: anything to cut, merge or move given ~6–7 chapters; where an expert gets
   bored or lost.
5. Reproducibility risks in a judge's fresh Colab run.
Keep it under ~2 pages.
