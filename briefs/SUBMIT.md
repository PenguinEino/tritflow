# SUBMIT stream brief: submission package for notebook v3

Work in `~/code-a-chip-v3`, editing only `submission/` and `docs/status/SUBMIT.md`. Do not commit.
Read `submission/README.md`, `submission/build_submission.py`, `submission/templates/*`,
`submission/official_sources.json`, `docs/author.md`, `docs/notebook-v3/STORYBOARD.md`.

The package currently builds from the v1 notebook (`notebook/tritflow_tr1um.ipynb`). Make it build
from v3: primary `notebook/v3/tritflow_en.ipynb` (being produced by the EN stream; until it exists,
develop against `notebook/v3/tritflow_ja.ipynb`) plus the Japanese companion
`notebook/v3/tritflow_ja.ipynb`, executed and packaged with the same rules (no placeholders, real
outputs, size budget, license/NOTICE, build-info with the pinned source commit).
1. Re-check the official rules (fetch the current README/FAQ/howtoapply of
   github.com/sscs-ose/sscs-ose-code-a-chip.github.io, update `official_sources.json`) and make the
   checklist match: team members at the top of the notebook, references, recommended tool versions,
   open license, project folder `ISSCC27/submitted_notebooks/<project>/`.
2. Draft README.md / ABSTRACT.md / PITCH.md for v3 in English: concept (balanced-ternary HDL → GDS on
   the open TR-1um PDK, cells from a taped-out 1-trit multiply-add, ternary-weight dot product as the
   running design), method, results (numbers only from executed notebook outputs; chapter 6 is still
   being written — wire the numbers so they are filled from the executed notebook, not typed), how to
   run on Colab, limits in one paragraph. No hype, no claim that ternary beats binary.
3. Keep `submission/tests` passing; add tests for the new inputs.
