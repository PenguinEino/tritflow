# NUMBERS stream brief: every number in the prose matches what the notebook computes

Report only: write `docs/status/NUMBERS.md`. Do not edit any other file. Do not commit.

Read `notebook/v3/narrative/*.md` (ja), `notebook/v3/narrative_en/*.md` (en), the code cells in
`notebook/v3/make_notebook.py`, `README.md`, `submission/templates/{PITCH,ABSTRACT,README}.md`.
Compare every stated number, count, unit and claim of a result (cell counts, areas, delays, currents,
voltages, error margins, coverage counts such as 6561, scaling-table values, pad counts, frame and pad
descriptions, chip/shuttle facts) with its source of truth: the executed outputs in
`notebook/v3/tritflow_{ja,en}_output.ipynb` if present, `results/*.json`, `notebook/assets/chip/dot4/`
(README, signoff.json, pad_map.json — the top was just moved into the stock OSS_FRAME with 16 pads, so
any remaining "probe pad", "TEG" or "17 pads" wording is stale), and the code that computes them.
Also check that the ja and en editions state the same numbers.

For each mismatch: file:line, the stated value, the true value with its source, and the exact
replacement text. List checked-and-consistent numbers only as a count. No style suggestions.
