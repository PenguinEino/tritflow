# README_TRIM stream brief: shorter submission README and no duplicated front matter

Work in `~/code-a-chip-v3`, only on `submission/templates/README.md`, `submission/build_submission.py`
(README filling and the `submission-identity` front cell only), `submission/results.py` if it only
serves the removed README tables, `submission/tests/`, and `docs/status/README_TRIM.md`.
Do not edit notebooks, narratives or notebook code. Do not commit. Do not rebuild the payload in
`submission/ISSCC27/` (the integrator does that last); use a temporary output directory for checks.

Read `docs/status/ACCEPTED.md` findings 2 (front matter part only) and 3, and the ISSCC27 call files the
builder records (rules commit a502a6b; `submission/` has the copies or URLs).

1. README: remove the "Concept and method" paragraph that repeats "Why ternary"; replace the
   `{{CHAPTER6_RESULTS}}` expansion (seven tables) with one sentence linking chapter 6 of the saved
   notebooks (en and ja); keep the compact dot4 result table if one exists; drop internal packaging
   commentary (how numbers are obtained, work-directory paths, the 12 MiB budget) — it stays in
   CHECKLIST/build-info. Keep authors, license, run instructions, Colab badge, recommended versions,
   measurement scope.
2. Front cell `submission-identity`: the notebook's own first cell already has the title, author and
   affiliation. Keep in the front cell only what the call requires there that the first cell lacks
   (check the ISSCC27 template: if it mandates an authors table at the top, keep that table and drop the
   duplicated title and prose author line from whichever place the template does not require). No new
   panels or boxes.
3. Remove code and tests that only served the removed tables; keep the rest passing
   (`python3 -m pytest -q submission`, except the two payload tests that compare with the not-yet-rebuilt
   payload). Build once into a temporary directory and read the generated README and the first two
   cells of each packaged notebook; report their line/word counts before and after.
